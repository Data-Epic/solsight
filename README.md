# solsight
Generate insight from solana transactions data

## Technologies Tools
- Docker
- Serverless
- Localstack
- IDE (VSCode, PyCharm, etc)

## Getting Started
git clone the repository 
```bash
git clone https://github.com/Data-Epic/solsight
```

If you don't have docker already installed, you can install it following the instructions [here](https://docs.docker.com/get-docker/)

If you don't have serverless already installed, you can install it following the instructions [here](https://www.serverless.com/framework/docs/getting-started)

## Using Virtual Environment
You can use any virtual environment of your choice (conda, poetry, virtualenv etc).
After creating a virtual environment. Run the following to install the libraries required to run the project.
```bash
pip3 install -r requirements.txt
```

## Deployment
Switch to serverless-file-setup branch. You can use `git fetch` to retrieve branch to local system.

start docker using the following command to run it in detached mode.
```bash
docker-compose up -d
```

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
