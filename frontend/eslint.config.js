import { dirname } from "path";
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
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn",
      "react/no-unescaped-entities": "off",
      "prefer-const": "warn",
      // Phase 24: Prevent unclickable buttons (Session 086)
      // jsx-a11y rules help catch interactive elements without proper handlers
      "jsx-a11y/interactive-supports-focus": "warn",
      "jsx-a11y/click-events-have-key-events": "warn",
      // CRITICAL: Enforce camelCase for API response types
      // The axios interceptor converts snake_case → camelCase, so TypeScript
      // interfaces MUST use camelCase or runtime access returns undefined.
      // See: Session 079, 080 which fixed 180+ violations across 41 files.
      "@typescript-eslint/naming-convention": [
        "warn",
        {
          selector: "typeProperty",
          format: ["camelCase"],
          leadingUnderscore: "allow",
          // Allow UPPER_CASE for constants in types
          filter: {
            regex: "^[A-Z][A-Z0-9_]*$",
            match: false,
          },
        },
        {
          selector: "objectLiteralProperty",
          format: ["camelCase"],
          leadingUnderscore: "allow",
          // Allow snake_case in specific contexts (API query params, etc.)
          filter: {
            regex: "^(Content-Type|Authorization|X-|_).*$",
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
    ],
  },
];

export default eslintConfig;
