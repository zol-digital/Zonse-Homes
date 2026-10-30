export const formatMWK = amount => `MWK ${Number(amount).toLocaleString("en-US")}`;

const PROPERTY_LABELS = { house: "House", apartment: "Apartment", land_plot: "Land / plot", commercial: "Commercial", other: "Other" };
export const propertyLabel = type => PROPERTY_LABELS[type] ?? "Other";

const PERIODS = { weekly: "per week", monthly: "per month", yearly: "per year" };
export function priceLabel(listing) {
  if (listing.intent === "rent") {
    return [formatMWK(listing.price), PERIODS[listing.rentalPeriod]].filter(Boolean).join(" ");
  }
  return formatMWK(listing.price) + (listing.negotiable ? " · negotiable" : "");
}

export const areaLabel = (value, unit) => `${Number(value).toLocaleString("en-US")} ${unit}`;

// Links are built only from digits, so no unexpected text can reach an href.
export function whatsappLink(number) {
  const digits = String(number ?? "").replace(/\D/g, "");
  return digits.length >= 9 ? `https://wa.me/${digits}` : null;
}
export function phoneLink(number) {
  const cleaned = String(number ?? "").replace(/[^\d+]/g, "");
  return /^\+?\d{9,15}$/.test(cleaned) ? `tel:${cleaned}` : null;
}
