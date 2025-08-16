#!/usr/bin/env python3
"""
DiagXpert Entry Point
Run the application or Workshop 4 demo
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "workshop4":
        # Run Workshop 4 demo
        from main import run_workshop4_demo
        run_workshop4_demo()
    else:
        # Run Flask application
        from main import app, config
        print("🚀 Starting DiagXpert Flask application...")
        print(f"🌐 Server will run on: http://{config.server.host}:{config.server.port}")
        print("📚 Workshop 4 features are ready!")
        print("💡 Use 'python run.py workshop4' to run Workshop 4 demo")
        print("=" * 60)
        
        try:
            app.run(
                host=config.server.host,
                port=config.server.port,
                debug=config.server.debug,
                use_reloader=config.server.use_reloader
            )
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        except Exception as e:
            print(f"❌ Application failed: {e}")
        finally:
            print("👋 DiagXpert shutdown complete")

if __name__ == "__main__":
    main()
