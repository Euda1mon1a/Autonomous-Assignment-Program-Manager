import { dirname } from "path";
import antiTrojanSource from "eslint-plugin-anti-trojan-source";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    plugins: {
      "anti-trojan-source": antiTrojanSource,
    },
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        caughtErrorsIgnorePattern: "^_",
        destructuredArrayIgnorePattern: "^_",
      }],
      "@typescript-eslint/no-explicit-any": "warn",
      "react/no-unescaped-entities": "off",
      "react/display-name": "off",
      "prefer-const": "warn",
      // Ensure useEffect/useMemo/useCallback dependency arrays are correct
      "react-hooks/exhaustive-deps": "warn",
      // Phase 24: Prevent unclickable buttons (Session 086)
      // jsx-a11y rules help catch interactive elements without proper handlers
      "jsx-a11y/interactive-supports-focus": "warn",
      "jsx-a11y/click-events-have-key-events": "warn",
      // CRITICAL: Enforce camelCase for API response types
      // The axios interceptor converts snake_case → camelCase, so TypeScript
      // interfaces MUST use camelCase or runtime access returns undefined.
      // See: Session 079, 080 which fixed 180+ violations across 41 files.
      // TODO: Promote to "error" after bulk naming-convention fix PR
      // GlassWorm/Trojan Source defense - detect invisible Unicode in source files
      "anti-trojan-source/no-bidi": "error",
      "@typescript-eslint/naming-convention": [
        "warn",
        {
          selector: "typeProperty",
          format: ["camelCase"],
          leadingUnderscore: "allow",
          // Allow UPPER_CASE constants and aria-* HTML attributes in types
          filter: {
            regex: "^[A-Z][A-Z0-9_]*$|^aria-",
            match: false,
          },
        },
        {
          selector: "objectLiteralProperty",
          format: ["camelCase"],
          leadingUnderscore: "allow",
          // Allow non-camelCase in specific contexts:
          // - HTTP headers (Content-Type, Authorization, X-*)
          // - Numeric keys (HTTP status codes, grid columns)
          // - CSS/Tailwind class name keys (gray-100, top-right, 2xl)
          // - aria-* attributes
          // - UPPER_CASE enum-like constant keys
          filter: {
            regex: "^(Content-Type|Authorization|X-|_|aria-).*$|^\\d+$|^[a-z]+-\\d+$|^\\d+[a-z]+$|^[A-Z][A-Z0-9_]*$",
            match: false,
          },
        },
      ],
    },
  },
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "out/**",
      "coverage/**",
      "*.config.js",
      "*.config.mjs",
      "src/types/api-generated.ts",
      "src/types/api-generated-check.ts",
    ],
  },
];

export default eslintConfig;
