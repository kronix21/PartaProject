document.addEventListener('DOMContentLoaded', () => {
    const avatarInput = document.getElementById('avatar-upload');
    const avatarPreview = document.getElementById('avatar-preview');

    if (avatarInput && avatarPreview) {
        avatarInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            
            if (file) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    avatarPreview.style.backgroundImage = `url(${e.target.result})`;
                    avatarPreview.style.backgroundColor = 'transparent'; 
                }
                
                reader.readAsDataURL(file);
            }
        });
    }
});