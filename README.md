# solsight
Generate insight from solana transactions data

## Getting Started
git clone the repository 
```bash
git clone https://github.com/Data-Epic/solsight
```

## Deployment
Switch to serverless-file-setup branch. You can use `git fetch` to retrieve branch to local system.

Run this in the root directory to deploy with serverless
```bash
sls deploy --stage local
```

To invoke the ingest function, run
```bash
sls invoke local --function ingest
```

To view the bucket details, open the url `http://localhost:4566/solsight-solana-io` in browser.

![list-bucket](/images/list-bucket.png)