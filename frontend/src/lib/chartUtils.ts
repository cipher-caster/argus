/**
 * Chart and Sparkline Utility Functions
 */

// Pseudo-random number generator seeded by string
function sfc32(a: number, b: number, c: number, d: number) {
  return function () {
    a >>>= 0;
    b >>>= 0;
    c >>>= 0;
    d >>>= 0;
    let t = (a + b) | 0;
    a = b ^ (b >>> 9);
    b = (c + (c << 3)) | 0;
    c = (c << 21) | (c >>> 11);
    d = (d + 1) | 0;
    t = (t + d) | 0;
    c = (c + t) | 0;
    return (t >>> 0) / 4294967296;
  };
}

export function generateDeterministicSparkline(symbol: string, basePrice: number, change: number) {
  // Create a seed from symbol components
  let h1 = 1779033703,
    h2 = 3144134277,
    h3 = 1013904242,
    h4 = 2773480762;
  for (let i = 0, k; i < symbol.length; i++) {
    k = symbol.charCodeAt(i);
    h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
    h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
    h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
    h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
  }

  const rand = sfc32(h1, h2, h3, h4);
  const points = 20;
  const data = [basePrice];
  let current = basePrice;

  // Bias trend based on 24h change
  const trendBias = change / points;

  for (let i = 1; i < points; i++) {
    const volatility = basePrice * 0.02; // 2% volatility
    const move = (rand() - 0.5) * volatility + trendBias * basePrice * 0.01;
    current += move;
    data.push(current);
  }
  return data;
}
