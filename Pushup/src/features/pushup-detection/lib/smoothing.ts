export class EmaSmoother {
  private current: number | null = null;
  private readonly alpha: number;

  constructor(alpha: number) {
    this.alpha = alpha;
  }

  next(value: number) {
    if (this.current === null) {
      this.current = value;
      return value;
    }

    this.current = this.alpha * value + (1 - this.alpha) * this.current;
    return this.current;
  }

  reset() {
    this.current = null;
  }
}
