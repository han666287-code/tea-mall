import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { addCartItem, deleteCartItem, getCartItems, updateCartItem } from '@/api/cart'
import { useAuthStore } from '@/store/auth'
import type { CartItem } from '@/types/cart'

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const loading = ref(false)

  const totalQuantity = computed(() =>
    items.value.reduce((sum, item) => sum + item.quantity, 0),
  )
  const totalPrice = computed(() =>
    items.value.reduce((sum, item) => sum + item.quantity * Number(item.product.price), 0),
  )

  async function fetchCart() {
    const authStore = useAuthStore()
    if (!authStore.token) {
      items.value = []
      return
    }
    loading.value = true
    try {
      const { data } = await getCartItems()
      items.value = data
    } finally {
      loading.value = false
    }
  }

  async function addToCart(productId: number, quantity = 1) {
    await addCartItem({ product_id: productId, quantity })
    await fetchCart()
  }

  async function updateQuantity(itemId: number, quantity: number) {
    await updateCartItem(itemId, quantity)
    await fetchCart()
  }

  async function removeItem(itemId: number) {
    await deleteCartItem(itemId)
    await fetchCart()
  }

  function clear() {
    items.value = []
  }

  return {
    items,
    loading,
    totalQuantity,
    totalPrice,
    fetchCart,
    addToCart,
    updateQuantity,
    removeItem,
    clear,
  }
})
