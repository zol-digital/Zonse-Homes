// Sample data only. Replace with GET /api/v1/listings when the API exists.
// Money is stored as whole MWK amounts, never floats.
export const listings = [
  {
    id: "zh-101", status: "published", intent: "rent", propertyType: "apartment",
    title: "Two-bedroom flat near the Area 3 market", price: 450000, rentalPeriod: "monthly", deposit: 900000,
    bedrooms: 2, bathrooms: 1, district: "Lilongwe", neighbourhood: "Area 3", precision: "neighbourhood",
    description: "Bright second-floor flat with a balcony, water tank and secure parking, close to the market and main bus route.",
    amenities: ["Water tank", "Secure parking", "Backup generator"],
    verification: ["Phone confirmed"],
    advertiser: { name: "Chikondi Properties", type: "agent", phone: "+265 999 000 111", whatsapp: "+265 999 000 111" },
    availabilityConfirmedAt: "22 Oct 2026", publishedAt: Date.parse("2026-10-20"), tone: "#c7d9cc"
  },
  {
    id: "zh-102", status: "published", intent: "sale", propertyType: "house",
    title: "Three-bedroom family home with garden", price: 95000000, negotiable: true,
    bedrooms: 3, bathrooms: 3, district: "Blantyre", neighbourhood: "Sunnyside", precision: "approximate",
    description: "Modern family house on a quiet road with a garden, double garage and borehole.",
    amenities: ["Borehole", "Double garage", "Garden"],
    verification: ["Email confirmed", "Agent identity reviewed"],
    advertiser: { name: "Mwale & Partners", type: "agency", phone: "+265 888 456 789", whatsapp: "" },
    availabilityConfirmedAt: "18 Oct 2026", publishedAt: Date.parse("2026-10-15"), tone: "#e8d5b5"
  },
  {
    id: "zh-103", status: "published", intent: "sale", propertyType: "land_plot",
    title: "Residential plot with road access", price: 5000000, negotiable: false,
    landArea: 1000, landAreaUnit: "m²", district: "Dedza", neighbourhood: "Dedza town", precision: "neighbourhood",
    description: "Level 1,000 m² plot with road access and electricity nearby. Ask the advertiser for ownership documents before paying.",
    amenities: ["Road access"],
    verification: ["Email confirmed"],
    advertiser: { name: "Tiyese Banda", type: "individual", phone: "+265 991 222 333", whatsapp: "+265 991 222 333" },
    availabilityConfirmedAt: "20 Oct 2026", publishedAt: Date.parse("2026-10-12"), tone: "#d6dfc2"
  },
  {
    id: "zh-104", status: "published", intent: "rent", propertyType: "commercial",
    title: "Ground-floor shop on the main road", price: 1200000, rentalPeriod: "monthly", deposit: 2400000,
    bathrooms: 1, buildingArea: 120, buildingAreaUnit: "m²", district: "Mzuzu", neighbourhood: "City Centre", precision: "neighbourhood",
    description: "120 m² shop with a glass front and storage room. Suitable for retail or an office.",
    amenities: ["Storage room", "Street frontage"],
    verification: [],
    advertiser: { name: "Nkhata Estates", type: "developer", phone: "+265 881 000 555", whatsapp: "" },
    availabilityConfirmedAt: "24 Oct 2026", publishedAt: Date.parse("2026-10-23"), tone: "#f0c9b5"
  }
];
