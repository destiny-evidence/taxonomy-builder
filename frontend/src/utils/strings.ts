/**
 * Convert a string to camelCase for use as an identifier.
 *
 * "Birth Date" -> "birthDate"
 * "my-cool-thing" -> "myCoolThing"
 */
export function toCamelCase(str: string): string {
  if (/^[a-zA-Z][a-zA-Z0-9]*$/.test(str)) {
    return str[0].toLowerCase() + str.slice(1);
  }
  let result = str
    .toLowerCase()
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, char) => char.toUpperCase())
    .replace(/^./, (char) => char.toLowerCase())
    .replace(/[^a-zA-Z0-9]/g, "");
  if (result && !result[0].match(/[a-zA-Z]/)) {
    result = "prop-" + result;
  }
  return result;
}

const IDENTIFIER_PATTERN = /^[a-zA-Z][a-zA-Z0-9_-]*$/;

/**
 * Validate a string as a URI-safe identifier.
 * Returns an error message or null if valid.
 */
export function validateIdentifier(value: string): string | null {
  if (!value.trim()) {
    return "Identifier is required";
  }
  if (!value[0].match(/[a-zA-Z]/)) {
    return "Identifier must start with a letter";
  }
  if (!IDENTIFIER_PATTERN.test(value)) {
    return "Identifier must be URI-safe: letters, numbers, underscores, and hyphens only";
  }
  return null;
}
