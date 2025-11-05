import { Rates } from "./api";

/**
 * Calculate price based on order specifications and current rates
 */
export function computePrice(
  order: {
    pages: number;
    copies: number;
    color: "bw" | "color";
    sides: "single" | "duplex";
    size: "A4" | "A3";
  },
  rates: Rates
): number {
  const { pages, copies, color, sides, size } = order;

  // Get base rate for A4
  let baseRate: number;
  if (color === "bw") {
    baseRate = sides === "duplex" ? rates.bwDuplexA4 : rates.bwSingleA4;
  } else {
    baseRate = sides === "duplex" ? rates.colorDuplexA4 : rates.colorSingleA4;
  }

  // A3 is typically 2x the A4 price
  if (size === "A3") {
    baseRate *= 2;
  }

  // Calculate total
  const total = pages * copies * baseRate;

  // Apply minimum charge
  return Math.max(total, rates.minCharge);
}

/**
 * Format price as currency string
 */
export function formatPrice(price: number): string {
  return `₹${price.toFixed(2)}`;
}
