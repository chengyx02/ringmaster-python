from ctypes import *

def get_vpx_versions():
    try:
        # Load libvpx
        libvpx = cdll.LoadLibrary('libvpx.so')
        
        # Get version info
        libvpx.vpx_codec_version.restype = c_int
        version = libvpx.vpx_codec_version()
        
        # Extract versions from packed integer
        vpx_version_major = (version >> 16) & 0xFF
        vpx_version_minor = (version >> 8) & 0xFF
        vpx_version_patch = version & 0xFF
        
        # Calculate ABI versions based on library version
        VPX_IMAGE_ABI_VERSION = vpx_version_major
        VPX_CODEC_ABI_VERSION = 4 + VPX_IMAGE_ABI_VERSION  
        VPX_EXT_RATECTRL_ABI_VERSION = 1
        VPX_ENCODER_ABI_VERSION = (vpx_version_major + 11) + VPX_CODEC_ABI_VERSION + VPX_EXT_RATECTRL_ABI_VERSION
        
        return {
            'IMAGE_ABI': VPX_IMAGE_ABI_VERSION,
            'CODEC_ABI': VPX_CODEC_ABI_VERSION,
            'EXT_RATECTRL_ABI': VPX_EXT_RATECTRL_ABI_VERSION,
            'ENCODER_ABI': VPX_ENCODER_ABI_VERSION
        }
    except Exception as e:
        raise RuntimeError(f"Failed to determine VPx versions: {e}")

# Replace hardcoded values with dynamic ones
vpx_versions = get_vpx_versions()
VPX_IMAGE_ABI_VERSION = vpx_versions['IMAGE_ABI']
VPX_CODEC_ABI_VERSION = vpx_versions['CODEC_ABI']
VPX_EXT_RATECTRL_ABI_VERSION = vpx_versions['EXT_RATECTRL_ABI']
VPX_ENCODER_ABI_VERSION = vpx_versions['ENCODER_ABI']

print("\n=== libvpx ABI Versions ===")
print(f"VPX_IMAGE_ABI_VERSION: {VPX_IMAGE_ABI_VERSION}")
print(f"VPX_CODEC_ABI_VERSION: {VPX_CODEC_ABI_VERSION}")
print(f"VPX_EXT_RATECTRL_ABI_VERSION: {VPX_EXT_RATECTRL_ABI_VERSION}")
print(f"VPX_ENCODER_ABI_VERSION: {VPX_ENCODER_ABI_VERSION}")
print("========================\n")