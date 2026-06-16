document.addEventListener('DOMContentLoaded', () => {
  // Mobile Navigation Menu Toggle
  const menuToggle = document.getElementById('menuToggle');
  const navMenu = document.getElementById('navMenu');
  
  if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', () => {
      menuToggle.classList.toggle('active');
      navMenu.classList.toggle('active');
    });
  }

  // 3-Step Assessment Form Manager
  const estimationForm = document.getElementById('estimationForm');
  if (estimationForm) {
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    
    const progressStep1 = document.getElementById('progressStep1');
    const progressStep2 = document.getElementById('progressStep2');
    const progressStep3 = document.getElementById('progressStep3');
    const progressLine1 = document.getElementById('progressLine1');
    const progressLine2 = document.getElementById('progressLine2');
    
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    const photoUpload = document.getElementById('photoUpload');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    
    // Live confirmation preview spans
    const confirmName = document.getElementById('confirmName');
    const confirmEmail = document.getElementById('confirmEmail');
    const confirmPhone = document.getElementById('confirmPhone');
    const confirmCategory = document.getElementById('confirmCategory');
    const confirmDetails = document.getElementById('confirmDetails');
    const confirmPhotoName = document.getElementById('confirmPhotoName');

    // Handle Image Preview
    if (photoUpload && imagePreview && previewImg) {
      photoUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          // Check file size (limit to 5MB)
          if (file.size > 5 * 1024 * 1024) {
            alert('ファイルのサイズは5MB以下にしてください。');
            photoUpload.value = '';
            imagePreview.style.display = 'none';
            return;
          }
          
          const reader = new FileReader();
          reader.onload = (event) => {
            previewImg.src = event.target.result;
            imagePreview.style.display = 'flex';
          };
          reader.readAsDataURL(file);
        } else {
          imagePreview.style.display = 'none';
        }
      });
    }

    // Client-side Validation helper
    function validateStep1() {
      const name = document.getElementById('name').value.trim();
      const email = document.getElementById('email').value.trim();
      const phone = document.getElementById('phone').value.trim();
      
      if (!name) {
        alert('お名前を入力してください。');
        document.getElementById('name').focus();
        return false;
      }
      if (!email) {
        alert('メールアドレスを入力してください。');
        document.getElementById('email').focus();
        return false;
      }
      // Basic email regex
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        alert('正しいメールアドレスを入力してください。');
        document.getElementById('email').focus();
        return false;
      }
      if (!phone) {
        alert('電話番号を入力してください。');
        document.getElementById('phone').focus();
        return false;
      }
      // Basic phone regex (at least 10 digits)
      const phoneRegex = /^\d{10,11}$|^\d{2,4}-\d{2,4}-\d{4}$/;
      if (!phoneRegex.test(phone.replace(/[-\s]/g, ''))) {
        alert('正しい電話番号を入力してください（ハイフンなしで10桁または11桁）。');
        document.getElementById('phone').focus();
        return false;
      }
      return true;
    }

    // Step 1 -> Step 2 (Confirmation)
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (!validateStep1()) return;
        
        // Populating confirmation review text
        if (confirmName) confirmName.textContent = document.getElementById('name').value;
        if (confirmEmail) confirmEmail.textContent = document.getElementById('email').value;
        if (confirmPhone) confirmPhone.textContent = document.getElementById('phone').value;
        
        const catSelect = document.getElementById('category');
        if (confirmCategory && catSelect) {
          confirmCategory.textContent = catSelect.options[catSelect.selectedIndex].text;
        }
        
        if (confirmDetails) {
          const detailsText = document.getElementById('details').value.trim();
          confirmDetails.textContent = detailsText ? detailsText : '（特になし）';
        }
        
        if (confirmPhotoName) {
          const file = photoUpload.files[0];
          confirmPhotoName.textContent = file ? file.name : '添付なし';
        }

        // DOM toggle
        step1.style.display = 'none';
        step2.style.display = 'block';
        
        progressStep1.classList.add('completed');
        progressStep2.classList.add('active');
        progressLine1.classList.add('active');
      });
    }

    // Step 2 -> Step 1 (Back)
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        step2.style.display = 'none';
        step1.style.display = 'block';
        
        progressStep1.classList.remove('completed');
        progressStep2.classList.remove('active');
        progressLine1.classList.remove('active');
      });
    }

    // Form Submission Handler
    estimationForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // Show loading state on submit button
      const originalSubmitText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `
        <svg class="animate-spin" style="width:16px; height:16px; margin-right:8px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
          <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg> 送信中...
      `;

      try {
        const formData = new FormData(estimationForm);
        const object = Object.fromEntries(formData);
        const json = JSON.stringify(object);
        
        const response = await fetch('https://api.web3forms.com/submit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: json
        });

        const resData = await response.json();
        
        if (resData.success) {
          // Step 2 -> Step 3 (Success Screen)
          step2.style.display = 'none';
          step3.style.display = 'block';
          
          progressStep2.classList.add('completed');
          progressStep3.classList.add('active');
          progressLine2.classList.add('active');
          
          // Reset Form
          estimationForm.reset();
          if (imagePreview) imagePreview.style.display = 'none';
        } else {
          alert('送信エラーが発生しました: ' + (resData.message || 'もう一度お試しください。'));
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalSubmitText;
        }
      } catch (error) {
        alert('通信エラーが発生しました。インターネット接続を確認してもう一度お試しください。');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalSubmitText;
      }
    });
  }
});
