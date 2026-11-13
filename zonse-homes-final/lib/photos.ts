export const MAX_PHOTOS = 6;

export const FEATURES: Record<string, string[]> = {
  Essentials: ["Wi-Fi", "Parking", "Water tank", "Borehole", "Backup generator", "Solar power", "Security guard", "Gated compound"],
  Comfort: ["Air conditioning", "Furnished", "Kitchen", "Balcony", "Garden", "Swimming pool", "Gym", "Lift"],
  "Short stay (Airbnb)": ["Breakfast included", "Hot water", "Smart TV", "Dedicated workspace", "Washing machine", "Self check-in"],
  "House rules": ["Pets allowed", "Children welcome", "Smoking allowed"],
};

// Resize and compress in the browser so photos stay small enough to save
export function compressImage(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      const img = new Image();
      img.onerror = reject;
      img.onload = () => {
        const scale = Math.min(1, 1000 / Math.max(img.width, img.height));
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);
        canvas.getContext("2d")!.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL("image/jpeg", 0.75));
      };
      img.src = reader.result as string;
    };
    reader.readAsDataURL(file);
  });
}