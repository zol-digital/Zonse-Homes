export type Purpose = "Rent" | "Sale";
export type Category = "House" | "Apartment" | "Airbnb" | "Land";

export type Listing = {
  id: string;
  owner: string;
  title: string;
  purpose: Purpose;
  category: Category;
  district: string;
  lat: number;
  lng: number;
  price: number;
  beds: number;
  baths: number;
  area: number;
  description: string;
  features: string[];
  photos: string[];
  promoted: number;
  created: number;
};

export type User = {
  id: string;
  name: string;
  email: string;
  password: string;
  phone: string;
  accountType: "Individual" | "Company";
  verified: boolean;
  regNumber: string;
  favorites: string[];
};

export type Message = {
  id: string;
  listingId: string;
  from: string;
  to: string;
  text: string;
  time: number;
};

export type Data = {
  users: User[];
  listings: Listing[];
  messages: Message[];
};

export const DISTRICTS: Record<string, [number, number]> = {
  Lilongwe: [-13.9626, 33.7741],
  Blantyre: [-15.7861, 35.0058],
  Mzuzu: [-11.4598, 34.0287],
  Zomba: [-15.3851, 35.3188],
  Mangochi: [-14.4783, 35.2644],
  Salima: [-13.7781, 34.442],
  Kasungu: [-13.0333, 33.4833],
  Karonga: [-9.9333, 33.9333],
  Dedza: [-14.3667, 34.3333],
  Liwonde: [-15.06, 35.2236],
  Nkhotakota: [-12.9274, 34.296],
  Mzimba: [-11.9, 33.6],
  "Nkhata Bay": [-11.6, 34.3],
  Ntcheu: [-14.8186, 34.6428],
  Balaka: [-14.9833, 34.95],
  Rumphi: [-11.0167, 33.8667],
  Chitipa: [-9.7, 33.27],
  "Monkey Bay": [-14.088, 34.9186],
};

export const CATEGORY_ICON: Record<Category, string> = {
  House: "🏡",
  Apartment: "🏢",
  Airbnb: "🛏️",
  Land: "🌍",
};

export const ADS = [
  { title: "Need movers in Lilongwe?", text: "Get free quotes from trusted moving partners." },
  { title: "Furnish your new home", text: "Affordable furniture delivered across Malawi." },
  { title: "Protect your property", text: "Simple home insurance plans for owners and landlords." },
];

export const money = (n: number) => "MWK " + Number(n).toLocaleString("en-US");

export const isPromoted = (l: Listing) => l.promoted > Date.now();

export function priceText(l: Listing) {
  const suffix = l.category === "Airbnb" ? " / night" : l.purpose === "Rent" ? " / month" : "";
  return money(l.price) + suffix;
}

export function tagText(l: Listing) {
  if (isPromoted(l)) return "⭐ Promoted";
  if (l.category === "Airbnb") return "Short stay";
  return l.purpose === "Rent" ? "For rent" : "For sale";
}

export function specsText(l: Listing) {
  return l.category === "Land"
    ? `${l.area.toLocaleString()} m² plot`
    : `${l.beds} bed · ${l.baths} bath · ${l.area} m²`;
}

const DEMO_ID = "u-demo";

type Seed = Omit<Listing, "id" | "owner" | "created" | "promoted" | "photos" | "features"> &
  Partial<Pick<Listing, "promoted" | "features">>;

function seed(n: number, o: Seed): Listing {
  const hourMs = 60 * 60 * 1000;
  const startMs = 1767225600000; // fixed date so the server and browser agree
  return {
    id: "l" + n,
    owner: DEMO_ID,
    created: startMs - n * hourMs,
    promoted: 0,
    photos: [],
    features: [],
    ...o,
  };
}

export function seedData(): Data {
  return {
    users: [
      {
        id: DEMO_ID,
        name: "Demo Agent",
        email: "agent@demo.mw",
        password: "demo123",
        phone: "+265 999 000 111",
        accountType: "Company",
        verified: true,
        regNumber: "MW-DEMO-001",
        favorites: [],
      },
    ],
    listings: [
      seed(1, { title: "Sunset Paradise", purpose: "Rent", category: "Apartment", district: "Lilongwe", lat: -13.9626, lng: 33.7741, price: 450000, beds: 1, baths: 1, area: 58, description: "Bright one-bedroom apartment close to the city centre, with secure parking and backup water." }),
      seed(2, { title: "Serenity Heights", purpose: "Sale", category: "House", district: "Blantyre", lat: -15.7861, lng: 35.0058, price: 95000000, beds: 3, baths: 3, area: 656, promoted: 2208988800000, description: "A spacious, modern family home in a quiet neighbourhood with a garden and a double garage." }),
      seed(3, { title: "Lakeside Getaway", purpose: "Rent", category: "Airbnb", district: "Mangochi", lat: -14.4783, lng: 35.2644, price: 85000, beds: 2, baths: 1, area: 90, description: "Cosy short-stay cottage a short walk from the lake. Fully furnished with Wi-Fi." }),
      seed(4, { title: "Tranquil Oaks", purpose: "Rent", category: "House", district: "Zomba", lat: -15.3851, lng: 35.3188, price: 380000, beds: 2, baths: 2, area: 120, description: "Two-bedroom house at the foot of the mountain, with a courtyard and water tank." }),
      seed(5, { title: "Open Land near Dedza", purpose: "Sale", category: "Land", district: "Dedza", lat: -14.3667, lng: 34.3333, price: 5000000, beds: 0, baths: 0, area: 10000, description: "Flat plot with road access, ideal for farming or building." }),
      seed(6, { title: "The Haven Residences", purpose: "Sale", category: "Apartment", district: "Mzuzu", lat: -11.4598, lng: 34.0287, price: 42000000, beds: 2, baths: 2, area: 140, description: "Modern second-floor apartment with a balcony, lift access and 24-hour security." }),
    ],
    messages: [],
  };
}