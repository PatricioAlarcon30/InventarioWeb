function openPopup() {
    var popup = document.getElementById('popup');
    if (popup) {
      popup.style.display = 'block';
    }
  }
  
  function closePopup() {
    var popup = document.getElementById('popup');
    if (popup) {
      popup.style.display = 'none';
    }
  }
  
  // Muestra la ventana emergente cuando hay mensajes flash
  window.onload = function () {
    var messages = document.querySelectorAll('.flashes li');
    if (messages.length > 0) {
      openPopup();
    }
  };
  