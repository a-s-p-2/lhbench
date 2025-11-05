# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LHBench is a comprehensive benchmark suite for evaluating Lakehouse storage systems (Delta Lake, Apache Iceberg, Apache Hudi) running on Apache Spark. It implements TPC-DS-based workloads and specialized benchmarks to measure performance characteristics of ACID transactional data lake systems.

## Build Commands

### Compile and Package

**Option 1: Automated (may have issues in WSL2):**
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
./run_sbt.sh assembly
```

**Option 2: Manual build (recommended for WSL2 issues):**
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
sbt assembly
```
When prompted "Create a new server? y/n (default y)", answer `n`.

This generates a fat JAR containing all dependencies in the `target/` directory. For WSL2 environments with persistent sbt server issues, you can manually build the JAR and upload it directly to your EMR cluster using scp instead of relying on the automated build process.

### Run Benchmarks
The primary interface is the Python runner script:
```bash
./run-benchmark.py --cluster-hostname <hostname> -i <ssh-key> --ssh-user <ssh-user> --cloud-provider <aws|gcp> --benchmark <benchmark-name>
```

### Clean Build Artifacts
```bash
find target -name "*.jar" -type f -delete
```

## Architecture

### Core Components

**Python Orchestration Layer** (`run-benchmark.py`, `scripts/benchmarks.py`):
- Defines benchmark specifications for different storage formats and workloads
- Handles cluster communication, JAR compilation/upload, and remote execution
- Manages benchmark lifecycle from compilation to result collection

**Scala Benchmark Framework** (`src/main/scala/benchmark/`):
- `Benchmark.scala`: Abstract base class providing query execution timing, JSON reporting, and Spark session management
- Format-specific implementations: `TPCDSBenchmark`, `FileCountBenchmark`, `MergeMicroBenchmark`, `IncrementalTPCDSBenchmark`
- `TPCDSBenchmarkQueries.scala`: Contains all 99 TPC-DS queries adapted for Lakehouse systems

**Storage Format Integration**:
- Delta Lake: Uses Delta-specific Spark configurations and catalog settings
- Iceberg: Configured with Iceberg Spark extensions and Hive metastore integration
- Hudi: Employs Hudi-specific serializers and catalog configurations

### Benchmark Types

1. **TPC-DS**: End-to-end query performance on 1GB/3TB datasets
2. **TPC-DS Refresh**: Tests MERGE operations with incremental updates (10 refreshes of 3% data each)
3. **File Count**: Metadata performance with varying file counts (1K-200K files)
4. **Merge Microbenchmark**: Fine-grained merge performance analysis with configurable update percentages

### Configuration Management

**Version Configuration** (`run-benchmark.py`):
- Spark 3.3.0, Delta 2.2.0, Iceberg 1.1.0, Hudi 0.12.0
- Benchmark specifications are dynamically generated for different scales and formats

**Cloud Provider Adaptations**:
- AWS: S3SingleDriverLogStore for Delta, S3 requester pays configuration
- GCP: GCSLogStore for Delta, Google Storage integration

## Development Workflow

### Adding New Benchmarks
1. Create benchmark specification class in `scripts/benchmarks.py` inheriting from appropriate base classes
2. Implement Scala benchmark class in `src/main/scala/benchmark/` extending `Benchmark`
3. Add benchmark name mapping in `run-benchmark.py` benchmarks dictionary

### Testing Changes
Use the `test` benchmark for quick validation:
```bash
./run-benchmark.py --cluster-hostname <hostname> -i <ssh-key> --ssh-user <ssh-user> --cloud-provider <provider> --benchmark test
```

### Result Analysis
Benchmarks generate both JSON and CSV reports:
- Detailed metrics: `<benchmark-id>-report.json`
- Query timing data: `<benchmark-id>-report.csv`
- Console output: `<benchmark-id>-out.txt`

## Special Considerations

### Cluster Requirements
- EMR 6.9.0 (Spark 3.3.0) with external Hive Metastore
- Master: i3.2xlarge, Workers: 16x i3.2xlarge for full-scale benchmarks
- 1x worker sufficient for 1GB testing

### Data Sources
- TPC-DS datasets available at `s3://devrel-delta-datasets/tpcds-2.13/`
- Requester pays bucket requiring proper AWS configuration
- 1GB (`tpcds_sf1_parquet`) and 3TB (`tpcds_sf3000_parquet`) scales available

### Merge-on-Read vs Copy-on-Write
The benchmark framework supports both strategies:
- CoW: Eager file rewriting, high write amplification, low read amplification
- MoR: Deferred reconciliation, low write amplification, high read amplification
- Configurable via `--table-mode` parameter in refresh and merge benchmarks