const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const usdWhole = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

export const money = (n: number) => usd.format(n);
export const moneyWhole = (n: number) => usdWhole.format(n);

export const shortDate = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString("en-US", { month: "short", day: "numeric" });

export const monthName = (yyyyMm: string, offset = 0) => {
  const [y, m] = yyyyMm.split("-").map(Number);
  return new Date(y, m - 1 + offset, 1).toLocaleDateString("en-US", { month: "long" });
};

export const accountType: Record<string, string> = {
  checking: "Checking",
  savings: "Savings",
  credit: "Credit card",
  investment: "Investing",
};
