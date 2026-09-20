// Shared helpers for the cart and checkout suites.

// The cart the current spec file is working against. Set by createCart(), read by
// anything that needs a cart id without creating one.
export let activeCartId = '';

export async function createCart(request: any): Promise<string> {
  const res = await request.post('/api/carts', { data: { customer: 'qa+cart@acme.test' } });
  activeCartId = (await res.json()).id;
  return activeCartId;
}

export function currentCart(): string {
  return activeCartId;
}
