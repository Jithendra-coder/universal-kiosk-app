import type { Product } from "@/lib/types";
import { menutapProductImage } from "@/lib/menutap-images";

const fallbackImages = {
  burger:
    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=85",
  pizza:
    "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=900&q=85",
  chicken:
    "https://images.unsplash.com/photo-1562967916-eb82221dfb92?auto=format&fit=crop&w=900&q=85",
  coffee:
    "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=900&q=85",
  drink:
    "https://images.unsplash.com/photo-1544145945-f90425340c7e?auto=format&fit=crop&w=900&q=85",
  dessert:
    "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=900&q=85",
  bakery:
    "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=900&q=85",
  grocery:
    "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=900&q=85",
  salad:
    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=900&q=85",
  retail:
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=900&q=85",
  salon:
    "https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=900&q=85",
  iceCream:
    "https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=900&q=85",
  generic:
    "https://images.unsplash.com/photo-1543353071-087092ec393a?auto=format&fit=crop&w=900&q=85",
};

export function fallbackProductImage(product: Pick<Product, "name" | "item_type">) {
  const menutapImage = menutapProductImage(product);
  if (menutapImage) return menutapImage;

  const value = `${product.name} ${product.item_type}`.toLowerCase();

  if (value.includes("burger") || value.includes("sandwich")) return fallbackImages.burger;
  if (value.includes("pizza")) return fallbackImages.pizza;
  if (value.includes("chicken") || value.includes("sausage") || value.includes("wings")) {
    return fallbackImages.chicken;
  }
  if (value.includes("coffee") || value.includes("latte") || value.includes("tea")) return fallbackImages.coffee;
  if (value.includes("juice") || value.includes("drink") || value.includes("cola")) return fallbackImages.drink;
  if (value.includes("ice cream") || value.includes("sundae") || value.includes("scoop") || value.includes("cone") || value.includes("gelato") || value.includes("milkshake")) {
    return fallbackImages.iceCream;
  }
  if (value.includes("cake") || value.includes("donut") || value.includes("dessert")) return fallbackImages.dessert;
  if (value.includes("bread") || value.includes("bakery") || value.includes("croissant")) return fallbackImages.bakery;
  if (value.includes("salad") || value.includes("bowl") || value.includes("fresh")) return fallbackImages.salad;
  if (product.item_type === "retail") return fallbackImages.retail;
  if (product.item_type === "service") return fallbackImages.salon;

  return fallbackImages.generic;
}
