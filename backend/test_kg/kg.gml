graph [
  directed 1
  node [
    id 0
    label "run_test_run"
    type "Run"
    run_id "test_run"
    timestamp "2025-09-27T21:13:46.816461"
    metadata [
      sample_id "test"
    ]
  ]
  node [
    id 1
    label "ref_1c07fa29"
    type "Reference"
    hash "1c07fa29f090f0386980fb3948770738ca1c7f8d712c40c3589260ce6b62656b"
    path "data/refs/grch37/chr21.fa"
  ]
  node [
    id 2
    label "aligner_bwa"
    type "Aligner"
    tag "bwa"
  ]
  node [
    id 3
    label "caller_bcftools"
    type "Caller"
    tag "bcftools"
  ]
  node [
    id 4
    label "vcf_missing"
    type "VCF"
    hash "missing"
    path "test.vcf"
  ]
  node [
    id 5
    label "annotator_vep_v101"
    type "Annotator"
    tool "vep"
    db_version "v101"
  ]
]
