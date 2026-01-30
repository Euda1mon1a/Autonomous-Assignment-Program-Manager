"""
SAML 2.0 Service Provider implementation.

Provides SAML 2.0 authentication flow including:
- SP metadata generation
- IdP metadata parsing
- Authentication request generation
- SAML response validation
- Attribute extraction and mapping
"""

import base64
import uuid
import zlib
from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

from app.auth.sso.config import SAMLConfig


class SAMLProvider:
    """
    SAML 2.0 Service Provider implementation.

    Implements the Service Provider role in SAML 2.0 authentication flow.
    Supports HTTP-Redirect and HTTP-POST bindings.
    """

    # SAML namespaces
    SAML_NS = "urn:oasis:names:tc:SAML:2.0:assertion"
    SAMLP_NS = "urn:oasis:names:tc:SAML:2.0:protocol"
    DS_NS = "http://www.w3.org/2000/09/xmldsig#"

    def __init__(self, config: SAMLConfig) -> None:
        """
        Initialize SAML provider.

        Args:
            config: SAML configuration
        """
        self.config = config

    def generate_authn_request(self) -> tuple[str, str]:
        """
        Generate SAML Authentication Request.

        Creates a SAML AuthnRequest for initiating SSO flow.

        Returns:
            Tuple of (request_id, redirect_url)
        """
        request_id = f"_saml_{uuid.uuid4()}"
        issue_instant = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Build AuthnRequest XML
        authn_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest
    xmlns:samlp="{self.SAMLP_NS}"
    xmlns:saml="{self.SAML_NS}"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    Destination="{self.config.idp_sso_url}"
    AssertionConsumerServiceURL="{self.config.acs_url}"
    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{self.config.entity_id}</saml:Issuer>
    <samlp:NameIDPolicy
        Format="{self.config.name_id_format}"
        AllowCreate="true"/>
</samlp:AuthnRequest>"""

        # Encode request for HTTP-Redirect binding
        encoded_request = self._encode_saml_request(authn_request)

        # Build redirect URL
        params = {"SAMLRequest": encoded_request}
        redirect_url = f"{self.config.idp_sso_url}?{urlencode(params)}"

        return request_id, redirect_url

    def parse_saml_response(
        self, saml_response: str, validate_signature: bool = True
    ) -> dict[str, Any]:
        """
        Parse and validate SAML response.

        Args:
            saml_response: Base64-encoded SAML response
            validate_signature: Whether to validate XML signature

        Returns:
            Dict containing user attributes and metadata

        Raises:
            ValueError: If response is invalid or signature verification fails
        """
        # Decode SAML response
        try:
            decoded_response = base64.b64decode(saml_response).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Failed to decode SAML response: {e}")

            # Parse XML
        try:
            root = ET.fromstring(decoded_response)
        except ET.ParseError as e:
            raise ValueError(f"Invalid SAML XML: {e}")

            # Validate response status
        self._validate_response_status(root)

        # Extract assertion
        assertion = self._extract_assertion(root)

        # Validate signature if required
        if validate_signature and (
            self.config.want_response_signed or self.config.want_assertions_signed
        ):
            self._validate_signature(root, assertion)

            # Validate conditions (NotBefore, NotOnOrAfter, AudienceRestriction)
        self._validate_conditions(assertion)

        # Extract and map attributes
        attributes = self._extract_attributes(assertion)

        # Extract NameID
        name_id = self._extract_name_id(assertion)

        # Extract session info
        session_index = self._extract_session_index(assertion)

        return {
            "name_id": name_id,
            "session_index": session_index,
            "attributes": attributes,
            "raw_response": decoded_response,
        }

    def generate_logout_request(
        self, name_id: str, session_index: str | None = None
    ) -> tuple[str, str]:
        """
        Generate SAML Logout Request.

        Args:
            name_id: NameID of user to logout
            session_index: Optional session index from authentication

        Returns:
            Tuple of (request_id, redirect_url)
        """
        request_id = f"_saml_logout_{uuid.uuid4()}"
        issue_instant = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        session_index_xml = ""
        if session_index:
            session_index_xml = (
                f"<samlp:SessionIndex>{session_index}</samlp:SessionIndex>"
            )

        logout_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:LogoutRequest
    xmlns:samlp="{self.SAMLP_NS}"
    xmlns:saml="{self.SAML_NS}"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    Destination="{self.config.idp_slo_url}">
    <saml:Issuer>{self.config.entity_id}</saml:Issuer>
    <saml:NameID Format="{self.config.name_id_format}">{name_id}</saml:NameID>
    {session_index_xml}
</samlp:LogoutRequest>"""

        encoded_request = self._encode_saml_request(logout_request)

        params = {"SAMLRequest": encoded_request}
        redirect_url = f"{self.config.idp_slo_url}?{urlencode(params)}"

        return request_id, redirect_url

    def generate_sp_metadata(self) -> str:
        """
        Generate Service Provider metadata XML.

        Returns:
            SP metadata XML string
        """
        metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    xmlns:ds="{self.DS_NS}"
    entityID="{self.config.entity_id}">
    <md:SPSSODescriptor
        AuthnRequestsSigned="{str(self.config.authn_requests_signed).lower()}"
        WantAssertionsSigned="{str(self.config.want_assertions_signed).lower()}"
        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>{self.config.name_id_format}</md:NameIDFormat>
        <md:AssertionConsumerService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="{self.config.acs_url}"
            index="0"
            isDefault="true"/>
        <md:SingleLogoutService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            Location="{self.config.slo_url}"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""

        return metadata

    def parse_idp_metadata(self, metadata_xml: str) -> dict[str, str]:
        """
        Parse Identity Provider metadata.

        Extracts IdP configuration from metadata XML.

        Args:
            metadata_xml: IdP metadata XML string

        Returns:
            Dict with IdP configuration (entity_id, sso_url, slo_url, x509_cert)

        Raises:
            ValueError: If metadata is invalid
        """
        try:
            root = ET.fromstring(metadata_xml)
        except ET.ParseError as e:
            raise ValueError(f"Invalid IdP metadata XML: {e}")

            # Define namespaces
        ns = {
            "md": "urn:oasis:names:tc:SAML:2.0:metadata",
            "ds": self.DS_NS,
        }

        # Extract entity ID
        entity_id = root.get("entityID")
        if not entity_id:
            raise ValueError("Missing entityID in IdP metadata")

            # Extract SSO URL
        sso_element = root.find(
            ".//md:IDPSSODescriptor/md:SingleSignOnService[@Binding='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect']",
            ns,
        )
        sso_url = sso_element.get("Location") if sso_element is not None else ""

        # Extract SLO URL
        slo_element = root.find(
            ".//md:IDPSSODescriptor/md:SingleLogoutService[@Binding='urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect']",
            ns,
        )
        slo_url = slo_element.get("Location") if slo_element is not None else ""

        # Extract X.509 certificate
        cert_element = root.find(
            ".//md:IDPSSODescriptor/md:KeyDescriptor/ds:KeyInfo/ds:X509Data/ds:X509Certificate",
            ns,
        )
        x509_cert = (
            cert_element.text.strip()
            if cert_element is not None and cert_element.text is not None
            else ""
        )

        return {
            "entity_id": entity_id,
            "sso_url": sso_url if sso_url else "",
            "slo_url": slo_url if slo_url else "",
            "x509_cert": x509_cert,
        }

    def _encode_saml_request(self, request_xml: str) -> str:
        """
        Encode SAML request for HTTP-Redirect binding.

        Args:
            request_xml: SAML request XML string

        Returns:
            Base64-encoded, deflated request string
        """
        # Deflate (compress)
        compressed = zlib.compress(request_xml.encode("utf-8"))[2:-4]
        # Base64 encode
        encoded = base64.b64encode(compressed).decode("utf-8")
        return encoded

    def _validate_response_status(self, root: ET.Element) -> None:
        """
        Validate SAML response status.

        Args:
            root: SAML response root element

        Raises:
            ValueError: If status is not Success
        """
        ns = {"samlp": self.SAMLP_NS}
        status = root.find(".//samlp:StatusCode", ns)

        if status is None:
            raise ValueError("Missing StatusCode in SAML response")

        status_value = status.get("Value", "")
        if not status_value.endswith(":Success"):
            status_message = root.find(".//samlp:StatusMessage", ns)
            message = (
                status_message.text if status_message is not None else "Unknown error"
            )
            raise ValueError(f"SAML authentication failed: {message}")

    def _extract_assertion(self, root: ET.Element) -> ET.Element:
        """
        Extract Assertion element from SAML response.

        Args:
            root: SAML response root element

        Returns:
            Assertion element

        Raises:
            ValueError: If assertion is missing
        """
        ns = {"saml": self.SAML_NS}
        assertion = root.find(".//saml:Assertion", ns)

        if assertion is None:
            raise ValueError("Missing Assertion in SAML response")

        return assertion

    def _validate_signature(self, response: ET.Element, assertion: ET.Element) -> None:
        """
        Validate XML signature on response or assertion.

        Note: This is a simplified implementation. In production, use
        a library like python3-saml or pysaml2 for proper signature validation.

        Args:
            response: SAML response element
            assertion: Assertion element

        Raises:
            ValueError: If signature validation fails
        """
        # Check if signature exists on response or assertion
        ns = {"ds": self.DS_NS}

        response_sig = response.find(".//ds:Signature", ns)
        assertion_sig = assertion.find(".//ds:Signature", ns)

        if self.config.want_response_signed and response_sig is None:
            raise ValueError("Response signature required but not found")

        if self.config.want_assertions_signed and assertion_sig is None:
            raise ValueError("Assertion signature required but not found")

            # Note: Actual signature verification requires cryptographic validation
            # This would typically be done using xmlsec library or similar
            # For production use, integrate python3-saml or pysaml2
        if not self.config.idp_x509_cert:
            raise ValueError("IdP X.509 certificate not configured")

    def _validate_conditions(self, assertion: ET.Element) -> None:
        """
        Validate SAML Conditions (time bounds and audience).

        Args:
            assertion: Assertion element

        Raises:
            ValueError: If conditions are not met
        """
        ns = {"saml": self.SAML_NS}
        conditions = assertion.find(".//saml:Conditions", ns)

        if conditions is None:
            return  # Conditions are optional

        now = datetime.utcnow()

        # Check NotBefore
        not_before = conditions.get("NotBefore")
        if not_before:
            not_before_dt = datetime.strptime(not_before, "%Y-%m-%dT%H:%M:%SZ")
            if now < not_before_dt:
                raise ValueError("Assertion not yet valid (NotBefore)")

                # Check NotOnOrAfter
        not_on_or_after = conditions.get("NotOnOrAfter")
        if not_on_or_after:
            not_on_or_after_dt = datetime.strptime(
                not_on_or_after, "%Y-%m-%dT%H:%M:%SZ"
            )
            if now >= not_on_or_after_dt:
                raise ValueError("Assertion expired (NotOnOrAfter)")

                # Check AudienceRestriction
        audience = conditions.find(".//saml:Audience", ns)
        if audience is not None and audience.text != self.config.entity_id:
            raise ValueError(
                f"Audience restriction violation: expected {self.config.entity_id}, got {audience.text}"
            )

    def _extract_attributes(self, assertion: ET.Element) -> dict[str, str]:
        """
        Extract and map attributes from assertion.

        Args:
            assertion: Assertion element

        Returns:
            Dict of mapped user attributes
        """
        ns = {"saml": self.SAML_NS}
        attributes: dict[str, Any] = {}

        attribute_statement = assertion.find(".//saml:AttributeStatement", ns)
        if attribute_statement is None:
            return attributes

        for attr in attribute_statement.findall(".//saml:Attribute", ns):
            name = attr.get("Name", "")
            value_elem = attr.find(".//saml:AttributeValue", ns)

            if value_elem is not None and name:
                value = value_elem.text or ""

                # Map attribute using configured mapping
                for saml_attr, user_field in self.config.attribute_map.items():
                    if name == saml_attr or name.endswith(f":{saml_attr}"):
                        attributes[user_field] = value
                        break

        return attributes

    def _extract_name_id(self, assertion: ET.Element) -> str:
        """
        Extract NameID from assertion.

        Args:
            assertion: Assertion element

        Returns:
            NameID value

        Raises:
            ValueError: If NameID is missing
        """
        ns = {"saml": self.SAML_NS}
        name_id = assertion.find(".//saml:NameID", ns)

        if name_id is None or not name_id.text:
            raise ValueError("Missing NameID in assertion")

        return name_id.text

    def _extract_session_index(self, assertion: ET.Element) -> str | None:
        """
        Extract SessionIndex from assertion.

        Args:
            assertion: Assertion element

        Returns:
            SessionIndex value or None
        """
        ns = {"saml": self.SAML_NS}
        authn_statement = assertion.find(".//saml:AuthnStatement", ns)

        if authn_statement is not None:
            return authn_statement.get("SessionIndex")

        return None
