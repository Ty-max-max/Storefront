import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

function App() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cart, setCart] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [showCart, setShowCart] = useState(false);
  const [customerEmail, setCustomerEmail] = useState('');

  useEffect(() => {
    fetchCategories();
    fetchProducts();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/categories`);
      const data = await response.json();
      setCategories(data.categories || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchProducts = async (category = null) => {
    try {
      setLoading(true);
      const url = category && category !== 'all' 
        ? `${API_BASE_URL}/api/products?category=${category}`
        : `${API_BASE_URL}/api/products`;
      
      const response = await fetch(url);
      const data = await response.json();
      setProducts(data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.product_id === product.id);
    if (existingItem) {
      setCart(cart.map(item => 
        item.product_id === product.id 
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, { 
        product_id: product.id, 
        name: product.name,
        price: product.price,
        quantity: 1 
      }]);
    }
    
    // Show success message
    alert(`${product.name} added to cart!`);
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity <= 0) {
      removeFromCart(productId);
    } else {
      setCart(cart.map(item => 
        item.product_id === productId 
          ? { ...item, quantity: newQuantity }
          : item
      ));
    }
  };

  const getTotalPrice = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0).toFixed(2);
  };

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
    fetchProducts(category);
  };

  const handleCheckout = async () => {
    if (cart.length === 0) {
      alert('Your cart is empty!');
      return;
    }

    if (!customerEmail) {
      alert('Please enter your email address');
      return;
    }

    try {
      const orderData = {
        items: cart.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity
        })),
        customer_email: customerEmail
      };

      const response = await fetch(`${API_BASE_URL}/api/paypal/create-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
      });

      const result = await response.json();
      
      if (result.status === 'READY_FOR_PAYPAL_INTEGRATION') {
        alert(`PayPal Integration Ready!\n\nOrder Total: $${getTotalPrice()}\n\nNext Steps:\n${result.next_steps.join('\n')}`);
      } else {
        // In a real scenario, this would redirect to PayPal
        alert('Order created successfully!');
      }

    } catch (error) {
      console.error('Error during checkout:', error);
      alert('Checkout failed. Please try again.');
    }
  };

  const CategoryCard = ({ category, isSelected, onClick }) => (
    <div 
      className={`category-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <img src={category.image_url} alt={category.name} className="category-image" />
      <div className="category-info">
        <h3>{category.name}</h3>
        <p>{category.description}</p>
        <div className="category-price">${category.price}</div>
      </div>
    </div>
  );

  const ProductCard = ({ product }) => (
    <div className="product-card">
      <img src={product.image_url} alt={product.name} className="product-image" />
      <div className="product-info">
        <h3>{product.name}</h3>
        <p className="product-description">{product.description}</p>
        <div className="product-footer">
          <span className="product-price">${product.price}</span>
          <button 
            className="add-to-cart-btn"
            onClick={() => addToCart(product)}
          >
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );

  const CartModal = () => (
    <div className="cart-modal" style={{ display: showCart ? 'flex' : 'none' }}>
      <div className="cart-content">
        <div className="cart-header">
          <h2>Shopping Cart</h2>
          <button className="close-cart" onClick={() => setShowCart(false)}>×</button>
        </div>
        
        {cart.length === 0 ? (
          <p>Your cart is empty</p>
        ) : (
          <>
            <div className="cart-items">
              {cart.map(item => (
                <div key={item.product_id} className="cart-item">
                  <div className="cart-item-info">
                    <span>{item.name}</span>
                    <span>${item.price}</span>
                  </div>
                  <div className="cart-item-controls">
                    <button onClick={() => updateQuantity(item.product_id, item.quantity - 1)}>-</button>
                    <span>{item.quantity}</span>
                    <button onClick={() => updateQuantity(item.product_id, item.quantity + 1)}>+</button>
                    <button 
                      className="remove-item"
                      onClick={() => removeFromCart(item.product_id)}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="cart-summary">
              <div className="total-price">Total: ${getTotalPrice()}</div>
              
              <div className="checkout-form">
                <input
                  type="email"
                  placeholder="Your email address"
                  value={customerEmail}
                  onChange={(e) => setCustomerEmail(e.target.value)}
                  className="email-input"
                />
                <button className="checkout-btn" onClick={handleCheckout}>
                  Proceed to PayPal
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );

  return (
    <div className="App">
      {/* Header */}
      <header className="header">
        <div className="container">
          <h1 className="logo">📚 Digital Store</h1>
          <nav className="nav">
            <button 
              className="cart-button"
              onClick={() => setShowCart(true)}
            >
              🛒 Cart ({cart.length})
            </button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h2>Professional Templates & Educational Books</h2>
            <p>Perfect for job seekers and parents who want the best for their children</p>
            <img 
              src="https://images.unsplash.com/photo-1753161029492-0644556055cf" 
              alt="Digital storefront" 
              className="hero-image"
            />
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="categories">
        <div className="container">
          <h2>Shop by Category</h2>
          <div className="category-filters">
            <button 
              className={selectedCategory === 'all' ? 'active' : ''}
              onClick={() => handleCategoryChange('all')}
            >
              All Products
            </button>
            {categories.map(category => (
              <button
                key={category.id}
                className={selectedCategory === category.id ? 'active' : ''}
                onClick={() => handleCategoryChange(category.id)}
              >
                {category.name}
              </button>
            ))}
          </div>
          
          <div className="categories-grid">
            {categories.map(category => (
              <CategoryCard
                key={category.id}
                category={category}
                isSelected={selectedCategory === category.id}
                onClick={() => handleCategoryChange(category.id)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Products */}
      <section className="products">
        <div className="container">
          <h2>
            {selectedCategory === 'all' ? 'All Products' : 
             categories.find(c => c.id === selectedCategory)?.name || 'Products'}
          </h2>
          
          {loading ? (
            <div className="loading">Loading products...</div>
          ) : (
            <div className="products-grid">
              {products.map(product => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>&copy; 2025 Digital Store - Professional Templates & Educational Books</p>
          <p>Perfect for job seekers and parents 📚✨</p>
        </div>
      </footer>

      {/* Cart Modal */}
      <CartModal />
    </div>
  );
}

export default App;