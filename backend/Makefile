.PHONY: setup seed backend frontend demo-annotation

setup:
	@echo "Setting up GIA environment..."
	python3 -m venv venv
	. venv/bin/activate && pip install fastapi uvicorn pydantic pandas numpy scipy duckdb networkx weasyprint reportlab
	@echo "Checking for required tools..."
	@which bwa > /dev/null && echo "✓ bwa found" || echo "⚠ bwa not found - SIMULATED MODE ENABLED"
	@which samtools > /dev/null && echo "✓ samtools found" || echo "⚠ samtools not found - SIMULATED MODE ENABLED"
	@which bcftools > /dev/null && echo "✓ bcftools found" || echo "⚠ bcftools not found - SIMULATED MODE ENABLED"
	@which vep > /dev/null && echo "✓ vep found" || echo "⚠ vep not found - SIMULATED MODE ENABLED"
	@echo "✓ Setup complete"

seed:
	@echo "Seeding data fixtures..."
	python scripts/verify_data.py
	@echo "✓ Data seeding complete"

backend:
	. venv/bin/activate && uvicorn api.main:app --reload

frontend:
	npm run dev

demo-annotation:
	@echo "Running annotation drift demo..."
	python scripts/demo_annotation.py