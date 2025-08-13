from OpenGL.GL import *
import logging

class OpenGLSafety:
    """Funciones seguras para OpenGL que manejan errores comunes"""
    
    @staticmethod
    def safe_line_width(width):
        """Set line width safely, checking GL limits"""
        try:
            # Get the supported line width range
            range_info = glGetFloatv(GL_LINE_WIDTH_RANGE)
            min_width, max_width = range_info[0], range_info[1]
            
            # Clamp the width to supported range
            safe_width = max(min_width, min(width, max_width))
            
            if safe_width != width:
                logging.debug(f"Clamped line width from {width} to {safe_width} (range: {min_width}-{max_width})")
            
            glLineWidth(safe_width)
            
        except Exception as e:
            logging.error(f"Error setting line width: {e}")
            # Fallback to default - clamp to safe range
            try:
                safe_width = max(1.0, min(width, 5.0))  # Conservative range
                glLineWidth(safe_width)
            except:
                try:
                    glLineWidth(1.0)
                except:
                    pass
    
    @staticmethod
    def safe_point_size(size):
        """Set point size safely, checking GL limits"""
        try:
            # Get the supported point size range
            range_info = glGetFloatv(GL_POINT_SIZE_RANGE)
            min_size, max_size = range_info[0], range_info[1]
            
            # Clamp the size to supported range
            safe_size = max(min_size, min(size, max_size))
            
            if safe_size != size:
                logging.debug(f"Clamped point size from {size} to {safe_size} (range: {min_size}-{max_size})")
            
            glPointSize(safe_size)
            
        except Exception as e:
            logging.error(f"Error setting point size: {e}")
            # Fallback to default - clamp to safe range
            try:
                safe_size = max(1.0, min(size, 64.0))  # Conservative range
                glPointSize(safe_size)
            except:
                try:
                    glPointSize(1.0)
                except:
                    pass

    @staticmethod
    def check_gl_errors(context="OpenGL operation"):
        """Check for OpenGL errors and log them"""
        try:
            error = glGetError()
            if error != GL_NO_ERROR:
                error_msg = {
                    GL_INVALID_ENUM: "GL_INVALID_ENUM",
                    GL_INVALID_VALUE: "GL_INVALID_VALUE", 
                    GL_INVALID_OPERATION: "GL_INVALID_OPERATION",
                    GL_OUT_OF_MEMORY: "GL_OUT_OF_MEMORY",
                    GL_INVALID_FRAMEBUFFER_OPERATION: "GL_INVALID_FRAMEBUFFER_OPERATION"
                }.get(error, f"Unknown error {error}")
                
                logging.warning(f"OpenGL error in {context}: {error_msg}")
                return error
            return GL_NO_ERROR
        except Exception as e:
            logging.error(f"Error checking GL errors: {e}")
            return GL_NO_ERROR

    @staticmethod
    def get_gl_info():
        """Get OpenGL implementation information for debugging"""
        try:
            info = {
                'vendor': glGetString(GL_VENDOR).decode() if glGetString(GL_VENDOR) else 'Unknown',
                'renderer': glGetString(GL_RENDERER).decode() if glGetString(GL_RENDERER) else 'Unknown',
                'version': glGetString(GL_VERSION).decode() if glGetString(GL_VERSION) else 'Unknown',
                'shading_language_version': glGetString(GL_SHADING_LANGUAGE_VERSION).decode() if glGetString(GL_SHADING_LANGUAGE_VERSION) else 'Unknown'
            }
            
            # Get line width range
            try:
                line_range = glGetFloatv(GL_LINE_WIDTH_RANGE)
                info['line_width_range'] = f"{line_range[0]:.1f} - {line_range[1]:.1f}"
            except:
                info['line_width_range'] = 'Unknown'
            
            # Get point size range
            try:
                point_range = glGetFloatv(GL_POINT_SIZE_RANGE)
                info['point_size_range'] = f"{point_range[0]:.1f} - {point_range[1]:.1f}"
            except:
                info['point_size_range'] = 'Unknown'
            
            return info
        except Exception as e:
            logging.error(f"Error getting GL info: {e}")
            return {'error': str(e)}

    @staticmethod
    def log_gl_info():
        """Log OpenGL information for debugging"""
        try:
            info = OpenGLSafety.get_gl_info()
            logging.info("OpenGL Information:")
            for key, value in info.items():
                logging.info(f"  {key}: {value}")
        except Exception as e:
            logging.error(f"Error logging GL info: {e}")

# Utility function to safely initialize OpenGL debugging
def init_opengl_debug():
    """Initialize OpenGL debugging - call this after GL context is created"""
    try:
        OpenGLSafety.log_gl_info()
        
        # Test GL operations
        OpenGLSafety.safe_line_width(2.0)
        OpenGLSafety.safe_point_size(5.0)
        
        error = OpenGLSafety.check_gl_errors("OpenGL debug initialization")
        if error == GL_NO_ERROR:
            logging.info("OpenGL debugging initialized successfully")
        else:
            logging.warning(f"OpenGL debugging initialized with errors: {error}")
            
    except Exception as e:
        logging.error(f"Error initializing OpenGL debug: {e}")