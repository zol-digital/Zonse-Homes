"use client";

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect, useRef } from "react";
import { priceText, type Listing } from "@/lib/data";

const esc = (s: string) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));

const shortPrice = (n: number) => (n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + "M" : Math.round(n / 1000) + "k");

export default function MapView({ listings }: { listings: Listing[] }) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null);

  // Create the map once
  useEffect(() => {
    if (!el.current) return;
    const m = L.map(el.current).setView([-13.5, 33.9], 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap",
    }).addTo(m);
    layer.current = L.layerGroup().addTo(m);
    map.current = m;
    return () => {
      m.remove();
      map.current = null;
      layer.current = null;
    };
  }, []);

  // Redraw the pins whenever the filtered list changes
  useEffect(() => {
    if (!map.current || !layer.current) return;
    layer.current.clearLayers();
    listings.forEach((l) => {
      const icon = L.divIcon({
        className: "",
        html: `<div class="price-pin">${shortPrice(l.price)}</div>`,
        iconSize: undefined,
      });
      L.marker([l.lat, l.lng], { icon }).bindPopup(
        `<strong>${esc(l.title)}</strong><br/>${esc(priceText(l))}<br/><a href="/listing/${esc(l.id)}">View property</a>`
      ).addTo(layer.current!);
    });
    if (listings.length) {
      map.current.fitBounds(
        L.latLngBounds(listings.map((l) => [l.lat, l.lng] as [number, number])).pad(0.2),
        { maxZoom: 12 }
      );
    }
  }, [listings]);

  return <div ref={el} className="map-canvas" />;
}