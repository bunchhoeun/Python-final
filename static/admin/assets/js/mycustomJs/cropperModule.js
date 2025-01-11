// cropperModule.js

function initializeCropper(imageId, aspectRatio = NaN) {
    // const imageElement = document.getElementById(imageId);
    if (!imageId) {
        console.error(`No image element found with ID ${imageId}`);
        return null;
    }

    // Initialize Cropper.js
    const cropper = new Cropper(imageId, {
        aspectRatio: aspectRatio,
    });

    // Compress function using Compressor.js
    function compressImage(dataURL, quality = 0.7) {
        return new Promise((resolve) => {
            const imageFile = dataURLtoFile(dataURL, "cropped-image.jpg");
            new Compressor(imageFile, {
                quality: quality,
                success: (compressedBlob) => {
                    resolve(URL.createObjectURL(compressedBlob));
                },
                error: (err) => {
                    console.error("Compression error:", err);
                    resolve(null);
                },
            });
        });
    }

    // Helper function to convert dataURL to File

    // Return an object with methods to get the cropped image data, compress it, or destroy the cropper instance
    return {
        getCroppedDataURL: (type = "image/jpeg") =>
            cropper.getCroppedCanvas({fillColor: "#fff"}).toDataURL(type),
        getCompressedCroppedDataURL: async () => {
            const croppedDataURL = cropper.getCroppedCanvas({fillColor: "#fff"}).toDataURL("image/jpeg");
            return await compressImage(croppedDataURL);
        },
        destroy: () => cropper.destroy(),
    };
}

function dataURLtoFile(dataurl, filename) {
    if (!dataurl || !dataurl.startsWith('data:')) {
        throw new Error("Invalid Data URL");
    }

    const arr = dataurl.split(',');
    const mimeMatch = arr[0].match(/:(.*?);/);
    if (!mimeMatch) {
        throw new Error("Invalid MIME type in Data URL");
    }

    const mime = mimeMatch[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);

    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, {type: mime});
}

// Export the function as a module
function compressFile(file, quality = 0.7) {
    return new Promise((resolve, reject) => {
        if (!(file instanceof File)) {
            reject(new Error("Provided input is not a File"));
            return;
        }

        new Compressor(file, {
            quality: quality,
            success: (compressedBlob) => {
                const compressedFile = new File([compressedBlob], file.name, {
                    type: file.type,
                    lastModified: Date.now(),
                });
                resolve(compressedFile);
            },
            error: (err) => {
                console.error("Compression error:", err);
                reject(err);
            },
        });
    });
}

// Export the functions as a module
export {dataURLtoFile, initializeCropper, compressFile};
