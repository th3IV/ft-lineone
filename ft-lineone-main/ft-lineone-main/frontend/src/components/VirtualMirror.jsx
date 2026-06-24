import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

function VirtualMirror({
  userImage,
  productImage,
  resultImage,
  loading,
  onUserImageUpload,
  onGenerate,
}) {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        const reader = new FileReader();
        reader.onload = (e) => onUserImageUpload(e.target.result, file);
        reader.readAsDataURL(file);
      }
    },
    [onUserImageUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg"] },
    maxFiles: 1,
    multiple: false,
  });

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2 text-center">Your Photo</h3>
          <div
            {...getRootProps()}
            className={`aspect-square flex items-center justify-center cursor-pointer rounded-lg ${
              isDragActive ? "bg-indigo-50 border-indigo-400" : "bg-gray-50"
            }`}
          >
            <input {...getInputProps()} />
            {userImage ? (
              <img src={userImage} alt="User" className="w-full h-full object-cover rounded-lg" />
            ) : isDragActive ? (
              <p className="text-indigo-600 text-sm text-center px-2">Drop your photo here</p>
            ) : (
              <div className="text-center px-4">
                <svg className="mx-auto h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="mt-2 text-sm text-gray-500">Drag & drop or click to upload</p>
              </div>
            )}
          </div>
        </div>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2 text-center">Product</h3>
          <div className="aspect-square flex items-center justify-center bg-gray-50 rounded-lg">
            {productImage ? (
              <img src={productImage} alt="Product" className="w-full h-full object-cover rounded-lg" />
            ) : (
              <p className="text-gray-400 text-sm">No product selected</p>
            )}
          </div>
        </div>

        <div className="border-2 border-gray-300 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2 text-center">Result</h3>
          <div className="aspect-square flex items-center justify-center bg-gray-50 rounded-lg relative">
            {loading ? (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
                <p className="mt-2 text-sm text-gray-500">Processing...</p>
              </div>
            ) : resultImage ? (
              <img src={resultImage} alt="Try-On Result" className="w-full h-full object-cover rounded-lg" />
            ) : (
              <p className="text-gray-400 text-sm">Waiting...</p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 text-center">
        <button
          onClick={onGenerate}
          disabled={!userImage || !productImage || loading}
          className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {loading ? "Generating..." : "Generate Try-On"}
        </button>
      </div>
    </div>
  );
}

export default VirtualMirror;
