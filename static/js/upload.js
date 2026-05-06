document.addEventListener('DOMContentLoaded', function () {
    const uploadBox = document.getElementById('uploadBox');
    const imageInput = document.getElementById('imageInput');
    const uploadForm = document.getElementById('uploadForm');
    const uploadError = document.getElementById('uploadError');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    const uploadPreviewWrapper = document.getElementById('uploadPreviewWrapper');
    const imagePreview = document.getElementById('imagePreview');
    const analyzeButton = document.getElementById('analyzeButton');
    const loadingText = document.getElementById('loadingText');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingStepMessage = document.getElementById('loadingStepMessage');
    const loadingSteps = [
        'Initializing model',
        'Processing image',
        'Predicting disease',
        'Preparing results'
    ];
    let loadingStepIndex = 0;
    let loadingIntervalId = null;

    if (!uploadBox || !imageInput || !uploadForm) {
        return;
    }


    // Animate confidence/progress bars on prediction result
    function animateConfidenceBars() {
        const bars = document.querySelectorAll('.confidence-bar .progress-bar');
        bars.forEach(function(bar) {
            const confidence = parseInt(bar.getAttribute('data-confidence'), 10) || 0;
            bar.style.width = '0%';
            setTimeout(function() {
                bar.style.width = confidence + '%';
            }, 200);
        });
    }

    // Fade-in effect for prediction/result section
    function fadeInPredictionSection() {
        const resultSection = document.getElementById('prediction-result');
        if (resultSection) {
            resultSection.classList.add('fade-in-section');
        }
    }

    // On page load, animate prediction bars and fade-in result if present
    window.addEventListener('load', function() {
        animateConfidenceBars();
        fadeInPredictionSection();
    });
    function setError(message) {
        if (!uploadError) return;
        uploadError.textContent = message;
        uploadError.classList.remove('d-none');
    }

    function clearError() {
        if (!uploadError) return;
        uploadError.textContent = '';
        uploadError.classList.add('d-none');
    }

    function showPreview(file) {
        if (!imagePreview || !uploadPreviewWrapper || !uploadPlaceholder) return;
        const reader = new FileReader();
        reader.onload = function (e) {
            imagePreview.src = e.target.result;
            uploadPreviewWrapper.classList.remove('d-none');
            uploadPlaceholder.classList.add('d-none');
        };
        reader.readAsDataURL(file);
    }

    function resetPreview() {
        if (!imagePreview || !uploadPreviewWrapper || !uploadPlaceholder) return;
        imagePreview.src = '';
        uploadPreviewWrapper.classList.add('d-none');
        uploadPlaceholder.classList.remove('d-none');
    }

    function isValidImageFile(file) {
        if (!file) return false;
        const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (allowedTypes.includes(file.type)) return true;

        const name = (file.name || '').toLowerCase();
        return name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png');
    }

    function handleFile(file) {
        if (!file) return;
        if (!isValidImageFile(file)) {
            setError('Please upload a valid image file (JPG, PNG, JPEG).');
            imageInput.value = '';
            resetPreview();
            return;
        }

        clearError();

        // Attach file to the hidden input so Flask can receive it
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        imageInput.files = dataTransfer.files;

        showPreview(file);
    }

    // Clicking the upload box triggers the hidden file input
    uploadBox.addEventListener('click', function () {
        imageInput.click();
    });

    // Native file input change
    imageInput.addEventListener('change', function () {
        const file = imageInput.files && imageInput.files[0];
        handleFile(file);
    });

    // Drag & Drop events
    ['dragenter', 'dragover'].forEach(evtName => {
        uploadBox.addEventListener(evtName, function (e) {
            e.preventDefault();
            e.stopPropagation();
            uploadBox.classList.add('drag-active');
        });
    });

    ['dragleave', 'dragend', 'drop'].forEach(evtName => {
        uploadBox.addEventListener(evtName, function (e) {
            e.preventDefault();
            e.stopPropagation();
            uploadBox.classList.remove('drag-active');
        });
    });

    uploadBox.addEventListener('drop', function (e) {
        const files = e.dataTransfer && e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFile(files[0]);
        }
    });

    // Form submission / loading state
    uploadForm.addEventListener('submit', function (e) {
        clearError();

        const file = imageInput.files && imageInput.files[0];
        if (!file) {
            e.preventDefault();
            setError('Please upload a valid image file (JPG, PNG, JPEG).');
            return;
        }
        if (!isValidImageFile(file)) {
            e.preventDefault();
            setError('Please upload a valid image file (JPG, PNG, JPEG).');
            return;
        }

        // Show loading state
        if (analyzeButton) {
            analyzeButton.disabled = true;
            analyzeButton.classList.add('disabled');
            analyzeButton.dataset.originalText = analyzeButton.innerText;
            analyzeButton.innerText = 'Analyzing...';
        }
        if (loadingText) {
            loadingText.classList.remove('d-none');
        }

        // Show full-screen loading overlay and rotate step messages
        if (loadingOverlay) {
            loadingOverlay.classList.remove('d-none');
            loadingStepIndex = 0;
            if (loadingStepMessage) {
                loadingStepMessage.textContent = loadingSteps[loadingStepIndex];
            }
            if (loadingIntervalId !== null) {
                clearInterval(loadingIntervalId);
            }
            loadingIntervalId = setInterval(function () {
                loadingStepIndex = (loadingStepIndex + 1) % loadingSteps.length;
                if (loadingStepMessage) {
                    loadingStepMessage.textContent = loadingSteps[loadingStepIndex];
                }
            }, 2000);
        }
    });
});

