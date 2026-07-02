# Server baseline for CISPO 2030/8760

Snapshot time: 2026-07-02 17:20-17:47 Asia/Shanghai.

## Hardware and operating system

| Item | Observed value |
|---|---|
| Host | `user-PowerEdge-T550` |
| OS | Ubuntu 20.04.6 LTS, kernel 5.15.0-139-generic |
| CPU | 2 x Intel Xeon Gold 5318Y, 24 cores/socket, 96 logical CPUs total |
| NUMA | 2 nodes |
| RAM | 125 GiB total; 83 GiB available at inventory time |
| Swap | 21 GiB total; 11 GiB used at inventory time |
| GPU | 2 x NVIDIA GeForce RTX 4090, 24 GiB each; not used by the Gurobi LP |
| Root filesystem | 219 GiB ext4; 41 GiB free |
| Storage filesystem | `/data`, 15 TiB NTFS/fuseblk; 4.3 TiB free |
| Open-file limit | 65,536 |

`/data` uses `fuseblk` with `allow_other`; normal Unix owner/mode isolation is not enforced. SSH keys and Gurobi license files must remain under `/home/zz2`, not `/data`.

## Runtime prepared

- Miniforge: `/home/zz2/.local/miniforge3`
- Environment: `/home/zz2/.local/envs/cispo-2030`
- Python: 3.11.15
- NumPy: 2.4.6
- pandas: 2.3.3
- SciPy: 1.17.1
- netCDF4: 1.7.4
- Zarr: 2.18.7
- numcodecs: 0.13.1
- psutil: 6.1.1
- `gurobipy`: not installed; license mechanism not configured

## Model fit and runtime guard

- Estimated model: 32,678,590 variables, 53,204,758 constraints, 738,317,504 nonzeros.
- Conservative memory estimate: 38.23 GiB.
- Configured Gurobi threads: 32.
- Build refuses to start below 64 GiB available RAM.
- Gurobi `SoftMemLimit`: 80 GiB.

The host is shared. The initial load average was about 9-11 and three other Python jobs used roughly 37 GiB RAM. Available memory, swap activity, and competing jobs must be checked immediately before a full build.
