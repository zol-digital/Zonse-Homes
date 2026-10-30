import { Badge } from "./Button.jsx";
import { areaLabel, priceLabel, propertyLabel } from "../lib/format.js";

export function ListingCard({ listing: l, onOpen }) {
  const facts = [
    l.bedrooms != null && `${l.bedrooms} bd`,
    l.bathrooms != null && `${l.bathrooms} ba`,
    l.landArea && areaLabel(l.landArea, l.landAreaUnit),
    l.buildingArea && areaLabel(l.buildingArea, l.buildingAreaUnit)
  ].filter(Boolean);

  return (
    <article className="listing-card">
      <button className="listing-card__open" onClick={() => onOpen(l.id)} aria-label={`View ${l.title}`}>
        <div className="listing-card__photo" style={{ background: l.tone }} role="img" aria-label="Photo placeholder" />
        <div className="listing-card__body">
          <div className="listing-card__tags">
            <Badge>{propertyLabel(l.propertyType)}</Badge>
            {l.verification.length > 0 && <Badge tone="success">{l.verification[0]}</Badge>}
          </div>
          <h3>{l.title}</h3>
          <p className="muted">{l.neighbourhood}, {l.district}</p>
          <p className="listing-card__price">{priceLabel(l)}</p>
          <p className="muted">{facts.join(" · ")}</p>
        </div>
      </button>
    </article>
  );
}
