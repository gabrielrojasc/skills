export function slug(name) {
  return name.trim().toLowerCase().replace(/\s+/g, "-");
}
