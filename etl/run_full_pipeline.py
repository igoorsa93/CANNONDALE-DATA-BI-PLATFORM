#!/usr/bin/env python3
"""
Cannondale Data Platform - Full ETL Pipeline
Orchestrates: Products -> Images -> Stores -> Sales -> Inventory -> Validation -> Export
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def run_step(name, script_path, env=None):
    """Run a pipeline step"""
    logger.info(f"=== Starting {name} ===")
    start = datetime.now()
    
    cmd = [sys.executable, str(script_path)]
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    
    result = subprocess.run(cmd, cwd=ROOT, env=merged_env, capture_output=True, text=True)
    
    duration = (datetime.now() - start).total_seconds()
    
    if result.returncode == 0:
        logger.info(f"✅ {name} completed in {duration:.1f}s")
        if result.stdout:
            logger.info(result.stdout[-500:])
        return True
    else:
        logger.error(f"❌ {name} failed after {duration:.1f}s")
        logger.error(result.stderr[-1000:])
        return False

def main():
    logger.info("🚀 CANNONDALE DATA PLATFORM - FULL PIPELINE")
    logger.info("=" * 60)
    
    pipeline_steps = [
        ("Load Products", "etl/load_products.py"),
        ("Load Images", "etl/load_images.py"),
        ("Generate Stores", "etl/generate_stores.py"),
        ("Generate Sales", "etl/generate_sales.py"),
        ("Generate Inventory", "etl/generate_inventory.py"),
        ("Run Validation", "etl/validate_data.py"),
        ("Export Excel", "etl/export_excel.py"),
        ("Generate Report", "etl/generate_report.py"),
    ]
    
    failed_steps = []
    
    for name, script in pipeline_steps:
        script_path = ROOT / script
        if not script_path.exists():
            logger.warning(f"⚠️  Script not found: {script}, skipping...")
            continue
        
        success = run_step(name, script_path)
        if not success:
            failed_steps.append(name)
            logger.error(f"Pipeline stopped at {name}")
            break
    
    logger.info("=" * 60)
    if failed_steps:
        logger.error(f"❌ PIPELINE FAILED - Failed steps: {', '.join(failed_steps)}")
        sys.exit(1)
    else:
        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
        sys.exit(0)

if __name__ == "__main__":
    main()