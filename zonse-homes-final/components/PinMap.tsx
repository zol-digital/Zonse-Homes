"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect, useRef } from "react";

type Props = {
  pin: { lat: number; lng: number } | null;
  onPick: (lat: number, lng: number) => void;
};

export default function PinMap({ pin, onPick }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const marker = useRef<L.Marker | null>(null);
  const onPickRef = useRef(onPick);
  onPickRef.current = onPick;

  useEffect(() => {
    if (!el.current) return;
    const start = pin ?? { lat: -13.5, lng: 33.9 };
    const m = L.map(el.current).setView([start.lat, start.lng], pin ? 15 : 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap",
    }).addTo(m);
    if (pin) marker.current = L.marker([pin.lat, pin.lng], { draggable: true }).addTo(m);
    m.on("click", (e) => onPickRef.current(e.latlng.lat, e.latlng.lng));
    map.current = m;
    return () => {
      m.remove();
      map.current = null;
      marker.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const m = map.current;
    if (!m) return;
    if (!pin) {
      if (marker.current) {
        marker.current.remove();
        marker.current = null;
      }
      return;
    }
    if (!marker.current) {
      marker.current = L.marker([pin.lat, pin.lng], { draggable: true }).addTo(m);
      marker.current.on("dragend", () => {
        const p = marker.current!.getLatLng();
        onPickRef.current(p.lat, p.lng);
      });
    } else {
      marker.current.setLatLng([pin.lat, pin.lng]);
    }
  }, [pin]);

  return <div ref={el} className="pin-map" />;
}