"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useRef, useState } from "react";
import { DISTRICTS, type Category, type Purpose } from "@/lib/data";
import { useStore } from "@/lib/store";
import { FEATURES, MAX_PHOTOS, compressImage } from "@/lib/photos";

// The pin map needs the browser, so it's loaded only on the client
const PinMap = dynamic(() => import("@/components/PinMap"), { ssr: false });

export default function PostPage() {
  return (
    <Suspense fallback={null}>
      <PostForm />
    </Suspense>
  );
}

function PostForm() {
  const params = useSearchParams();
  const router = useRouter();
  const { me, listings, saveListing } = useStore();
  const editId = params.get("id") ?? undefined;

  if (!me) {
    return (
      <div className="empty">
        <div className="big">🏡</div>
        <p>Log in to post a listing.</p>
        <br />
        <Link className="btn" href="/account">Log in</Link>
      </div>
    );
  }

  // Only the owner can edit a listing
  const existing = editId
    ? listings.find((l) => l.id === editId && l.owner === me.id)
    : undefined;

  return (
    <PostFormInner
      key={existing?.id ?? "new"}
      existing={existing}
      onSave={(input) => {
        const id = saveListing(input, existing?.id);
        if (id) router.push("/mine");
      }}
    />
  );
}

type Input = Parameters<ReturnType<typeof useStore>["saveListing"]>[0];

function PostFormInner({
  existing,
  onSave,
}: {
  existing?: ReturnType<typeof useStore>["listings"][number];
  onSave: (input: Input) => void;
}) {
  const v = existing;
  const [title, setTitle] = useState(v?.title ?? "");
  const [purpose, setPurpose] = useState<Purpose>(v?.purpose ?? "Rent");
  const [category, setCategory] = useState<Category>(v?.category ?? "House");
  const [district, setDistrict] = useState(v?.district ?? "Lilongwe");
  const [price, setPrice] = useState(v ? String(v.price) : "");
  const [beds, setBeds] = useState(v ? String(v.beds) : "");
  const [baths, setBaths] = useState(v ? String(v.baths) : "");
  const [area, setArea] = useState(v ? String(v.area) : "");
  const [description, setDescription] = useState(v?.description ?? "");
  const [features, setFeatures] = useState<string[]>(v?.features ?? []);
  const [photos, setPhotos] = useState<string[]>(v?.photos ?? []);
  const [pin, setPin] = useState<{ lat: number; lng: number } | null>(
    v ? { lat: v.lat, lng: v.lng } : null
  );
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function addPhotos(files: FileList | null) {
    if (!files) return;
    const room = MAX_PHOTOS - photos.length;
    const chosen = Array.from(files).filter((f) => f.type.startsWith("image/")).slice(0, Math.max(room, 0));
    const added: string[] = [];
    for (const f of chosen) {
      try {
        added.push(await compressImage(f));
      } catch {}
    }
    setPhotos((p) => [...p, ...added].slice(0, MAX_PHOTOS));
    if (fileRef.current) fileRef.current.value = "";
  }

  function toggleFeature(f: string) {
    setFeatures((list) => (list.includes(f) ? list.filter((x) => x !== f) : [...list, f]));
  }

  function submit() {
    const c = DISTRICTS[district];
    const p = Number(price);
    if (!title.trim() || !p || !description.trim()) {
      return setError("Please fill in the title, price and description.");
    }
    setError("");
    onSave({
      title: title.trim(),
      purpose,
      category,
      district,
      lat: pin ? pin.lat : c[0],
      lng: pin ? pin.lng : c[1],
      price: p,
      beds: Number(beds) || 0,
      baths: Number(baths) || 0,
      area: Number(area) || 0,
      description: description.trim(),
      features,
      photos,
    });
  }

  return (
    <div className="card" style={{ maxWidth: 740 }}>
      <h2 style={{ fontSize: 26, marginBottom: 6 }}>{existing ? "Edit listing" : "Create a listing"}</h2>
      <p className="muted" style={{ marginBottom: 18 }}>Listing is free. You can promote it later to appear first.</p>

      <div className="field">
        <label>Title</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Modern 3-bed house in Area 25" />
      </div>

      <div className="row2">
        <div className="field">
          <label>I want to</label>
          <select className="select" value={purpose} onChange={(e) => setPurpose(e.target.value as Purpose)}>
            <option>Rent</option>
            <option>Sale</option>
          </select>
        </div>
        <div className="field">
          <label>Property type</label>
          <select className="select" value={category} onChange={(e) => setCategory(e.target.value as Category)}>
            <option>House</option>
            <option>Apartment</option>
            <option>Airbnb</option>
            <option>Land</option>
          </select>
        </div>
      </div>

      <div className="row2">
        <div className="field">
          <label>Location (district)</label>
          <select className="select" value={district} onChange={(e) => setDistrict(e.target.value)}>
            {Object.keys(DISTRICTS).map((d) => (
              <option key={d}>{d}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Price (MWK)</label>
          <input type="number" min="0" value={price} onChange={(e) => setPrice(e.target.value)} />
        </div>
      </div>

      <div className="row2">
        <div className="field">
          <label>Bedrooms</label>
          <input type="number" min="0" value={beds} onChange={(e) => setBeds(e.target.value)} />
        </div>
        <div className="field">
          <label>Bathrooms</label>
          <input type="number" min="0" value={baths} onChange={(e) => setBaths(e.target.value)} />
        </div>
      </div>

      <div className="field">
        <label>Size (m²)</label>
        <input type="number" min="0" value={area} onChange={(e) => setArea(e.target.value)} />
      </div>

      <div className="field">
        <label>Photos (up to {MAX_PHOTOS}, optional)</label>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          multiple
          disabled={photos.length >= MAX_PHOTOS}
          onChange={(e) => addPhotos(e.target.files)}
        />
        <div className="photo-strip">
          {photos.map((src, i) => (
            <div key={i} className="photo-thumb">
              <img src={src} alt={`Photo ${i + 1}`} />
              <button
                className="photo-x"
                onClick={() => setPhotos((p) => p.filter((_, j) => j !== i))}
                aria-label="Remove photo"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
        <p className="muted">{photos.length} of {MAX_PHOTOS} photos</p>
      </div>

      <div className="field">
        <label>Features (tick everything that applies)</label>
        {Object.entries(FEATURES).map(([group, items]) => (
          <div key={group} style={{ marginTop: 6 }}>
            <p className="muted" style={{ marginBottom: 6 }}>{group}</p>
            <div className="feature-chips">
              {items.map((f) => (
                <button
                  key={f}
                  type="button"
                  className={`chip ${features.includes(f) ? "active" : ""}`}
                  onClick={() => toggleFeature(f)}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="field">
        <label>Pin the property on the map</label>
        <PinMap pin={pin} onPick={(lat, lng) => setPin({ lat, lng })} />
        <div className="inline" style={{ marginTop: 8 }}>
          <button type="button" className="btn btn-light btn-small" onClick={() => setPin(null)}>
            Clear pin
          </button>
          <span className="muted">
            {pin
              ? `Pinned at ${pin.lat.toFixed(5)}, ${pin.lng.toFixed(5)}`
              : "No pin yet. The district centre will be used."}
          </span>
        </div>
      </div>

      <div className="field">
        <label>Description</label>
        <textarea className="textarea" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>

      {error && <p style={{ color: "var(--danger)", marginBottom: 12, fontSize: 14 }}>{error}</p>}

      <div className="inline">
        <button className="btn" onClick={submit}>{existing ? "Save changes" : "Publish listing"}</button>
        <Link className="btn btn-light" href="/mine">Cancel</Link>
      </div>
    </div>
  );
}