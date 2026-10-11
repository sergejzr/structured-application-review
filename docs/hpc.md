# HPC / SLURM mode

The analysis code is independent of the scheduler. On a GPU node, install the
HPC extra in an environment compatible with the cluster's CUDA and MinerU
installation:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[hpc]'
```

Set the OpenWebUI variables through the cluster's secret mechanism, never in a
committed script:

```bash
export OPENWEBUI_API_BASE='https://approved-openwebui.example/api'
export OPENWEBUI_API_KEY='...'
export OPENWEBUI_MODEL='local.DeepSeek-V4-Flash'
```

Then submit the same CLI command from a GPU allocation:

```bash
bewerbungsanalyse --input input --output output --ocr-backend mineru
```

For large batches, distribute the OCR and per-applicant LLM stages through the
site's scheduler. Keep `output/markdown/` and the JSON artifacts on persistent
storage so failed downstream stages can resume without repeating OCR.

Resource flags, partitions, GPU types, wall time, and MinerU model caches are
site-specific and must be supplied by the local cluster configuration.
