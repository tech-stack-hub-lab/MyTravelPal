document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.checkout-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        const res = await fetch(form.action, { method: 'POST', body: fd, headers: {'X-Requested-With': 'XMLHttpRequest'} });
        const data = await res.json();
        if (data.url) {
          window.location.href = data.url;
        } else {
          alert(data.error || 'Could not start checkout');
        }
      } catch (err) {
        alert('Checkout failed');
      }
    });
  });
});