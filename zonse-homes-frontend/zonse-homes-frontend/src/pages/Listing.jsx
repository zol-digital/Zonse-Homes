import { Badge, Button } from "../components/Button.jsx";
import { areaLabel, formatMWK, phoneLink, priceLabel, propertyLabel, whatsappLink } from "../lib/format.js";

export default function Listing({ listing: l, onBack }) {
  const wa = whatsappLink(l.advertiser.whatsapp);
  const tel = phoneLink(l.advertiser.phone);
  const facts = [
    ["Property type", propertyLabel(l.propertyType)],
    ["Bedrooms", l.bedrooms],
    ["Bathrooms", l.bathrooms],
    ["Land area", l.landArea && areaLabel(l.landArea, l.landAreaUnit)],
    ["Building area", l.buildingArea && areaLabel(l.buildingArea, l.buildingAreaUnit)],
    ["Deposit", l.deposit && formatMWK(l.deposit)]
  ].filter(([, value]) => value != null && value !== false);

  return (
    <div className="page">
      <button className="back" onClick={onBack}>← Back to results</button>
      <div className="listing-layout">
        <div>
          <div className="gallery" style={{ background: l.tone }} role="img" aria-label="Photo placeholder" />
          <h1>{l.title}</h1>
          <p className="muted">
            {l.neighbourhood}, {l.district}, Malawi
            {l.precision !== "exact" && " · approximate location shown"}
          </p>
          <div className="facts">
            {facts.map(([label, value]) => (
              <div key={label}><span className="muted">{label}</span><strong>{value}</strong></div>
            ))}
          </div>
          <h2>About this property</h2>
          <p>{l.description}</p>
          {l.amenities.length > 0 && (
            <>
              <h2>Amenities</h2>
              <ul>{l.amenities.map(a => <li key={a}>{a}</li>)}</ul>
            </>
          )}
        </div>

        <aside className="side-card">
          <p className="price-big">{priceLabel(l)}</p>
          <p className="muted">Availability last confirmed {l.availabilityConfirmedAt}</p>

          <h3>Verification</h3>
          {l.verification.length > 0 ? (
            <ul className="badges">
              {l.verification.map(v => <li key={v}><Badge tone="success">{v}</Badge></li>)}
            </ul>
          ) : <p className="muted">No checks completed yet.</p>}
          <p className="fine">Labels cover only the checks listed. They do not confirm legal title or ownership.</p>

          <h3>{l.advertiser.name}</h3>
          <p className="muted">{l.advertiser.type} advertiser</p>

          <div className="stack">
            {wa && <a className="btn btn--primary btn--md" href={wa} target="_blank" rel="noopener noreferrer">Message on WhatsApp</a>}
            {tel && <a className="btn btn--secondary btn--md" href={tel}>Call advertiser</a>}
            {!wa && !tel && <p className="muted">No contact method is publicly shown.</p>}
          </div>
          <Button variant="ghost" size="sm" disabled title="Reporting opens in Phase 3">Report this listing</Button>
        </aside>
      </div>
    </div>
  );
}
