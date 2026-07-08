export function normalizeGender(value) {
  const v = (value || "").toLowerCase().trim();
  if (["hombre", "men", "masculino", "male"].includes(v)) return "hombre";
  if (["mujer", "women", "femenino", "female"].includes(v)) return "mujer";
  if (["unisex", "unisexual"].includes(v)) return "unisex";
  return v;
}

export function normalizeGenderLabel(value) {
  const v = normalizeGender(value);
  if (v === "hombre") return "Hombre";
  if (v === "mujer") return "Mujer";
  if (v === "unisex") return "Unisex";
  return v;
}
