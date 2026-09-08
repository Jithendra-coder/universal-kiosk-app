import type { BusinessType, Product } from "@/lib/types";

const MENUTAP_IMAGE_ROOT = "/menutap-images";

const businessFolders: Record<BusinessType, string> = {
  restaurant: "restaurant",
  cafe: "cafe",
  retail: "retail_store",
  bakery: "bakery",
  pizza: "pizza",
  burger: "burger",
  grocery: "grocery",
  salon: "salon",
  ice_cream: "ice_cream",
  other: "other",
};

const keywordImages: Array<[string[], BusinessType, string]> = [
  [["margherita"], "pizza", "margherita_pizza.png"],
  [["pepperoni"], "pizza", "pepperoni_pizza.png"],
  [["garlic bread"], "pizza", "garlic_bread.png"],
  [["cheese burst"], "pizza", "cheese_burst_pizza.png"],
  [["pizza"], "pizza", "margherita_pizza.png"],
  [["burger copy", "classic burger", "veg burger"], "burger", "classic_veg_burger.png"],
  [["cheese burger"], "burger", "cheese_burger.png"],
  [["chicken burger"], "burger", "chicken_burger.png"],
  [["fries", "french fries"], "burger", "french_fries.png"],
  [["milkshake"], "burger", "chocolate_milkshake.png"],
  [["biryani"], "restaurant", "chicken_biryani.png"],
  [["butter chicken"], "restaurant", "butter_chicken.png"],
  [["paneer"], "restaurant", "paneer_tikka.png"],
  [["fried rice"], "restaurant", "veg_fried_rice.png"],
  [["dosa"], "restaurant", "masala_dosa.png"],
  [["latte", "coffee", "cappuccino"], "cafe", "cappuccino.png"],
  [["sandwich"], "cafe", "veg_sandwich.png"],
  [["brownie"], "cafe", "chocolate_brownie.png"],
  [["juice", "drink"], "grocery", "orange_juice.png"],
  [["croissant"], "bakery", "butter_croissant.png"],
  [["cake"], "bakery", "chocolate_cake.png"],
  [["donut"], "bakery", "donut.png"],
  [["bread"], "grocery", "bread.png"],
  [["apple"], "grocery", "apples.png"],
  [["banana"], "grocery", "bananas.png"],
  [["milk"], "grocery", "milk.png"],
  [["rice"], "grocery", "rice.png"],
  [["haircut", "hair cut"], "salon", "haircut_service.png"],
  [["facial"], "salon", "facial_service.png"],
  [["spa"], "salon", "hair_spa.png"],
  [["styling"], "salon", "hair_styling.png"],
  [["manicure", "nails"], "salon", "manicure.png"],
  [["sundae"], "ice_cream", "brownie_sundae.png"],
  [["cone"], "ice_cream", "ice_cream_cone.png"],
  [["ice cream", "scoop"], "ice_cream", "vanilla_ice_cream.png"],
  [["tshirt", "shirt"], "retail", "black_tshirt.png"],
  [["sneaker", "shoe", "footwear"], "retail", "white_sneakers.png"],
  [["headphone"], "retail", "headphones.png"],
  [["perfume"], "retail", "perfume.png"],
  [["gift"], "other", "gift_box.png"],
  [["notebook"], "other", "notebook.png"],
];

export function isMenuTapStaticImage(path?: string | null) {
  if (!path) return false;
  return path.startsWith(`${MENUTAP_IMAGE_ROOT}/`) || path.startsWith("menutap-images/");
}

export function menutapBusinessPreviewImage(type: BusinessType) {
  const folder = businessFolders[type] ?? businessFolders.other;
  return `${MENUTAP_IMAGE_ROOT}/${folder}/${folder}_preview.png`;
}

export function menutapProductImage(product: Pick<Product, "name" | "item_type">) {
  const value = `${product.name} ${product.item_type}`.toLowerCase();
  const match = keywordImages.find(([keywords]) => keywords.some((keyword) => value.includes(keyword)));
  if (match) return imagePath(match[1], match[2]);
  if (product.item_type === "service") return imagePath("salon", "haircut_service.png");
  if (product.item_type === "retail") return imagePath("retail", "black_tshirt.png");
  return imagePath("other", "gift_box.png");
}

function imagePath(type: BusinessType, image: string) {
  const folder = businessFolders[type] ?? businessFolders.other;
  return `${MENUTAP_IMAGE_ROOT}/${folder}/${image}`;
}

export function menutapImagePath(type: BusinessType, image: string) {
  return imagePath(type, image);
}
