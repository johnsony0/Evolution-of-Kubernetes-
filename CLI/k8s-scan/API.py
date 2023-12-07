from fastapi import FastAPI
from neo4j import GraphDatabase, RoutingControl

def init():
    #initialize neo4j
    uri = "neo4j+s://e434d27c.databases.neo4j.io"
    username = "neo4j"
    password = "X7ADNYHwX-VsBYl_E2d7uKbGcRjvLoVOGSytze9OpHA"
    driver= GraphDatabase.driver(uri, auth=(username, password))
    return driver

app = FastAPI()

@app.get("/dep/{version}")
def dep(version: str):
    driver = init()
    records,summary,keys = driver.execute_query(
        "MATCH (:KubeVersion{kubernetesVersion:$version})-[:Depends_On]->(p) return p.dependencyName,p.dependencyVersion",
        {"version":version}, routing = RoutingControl.READ, database = "neo4j"
    )
    driver.close()
    return records

@app.get("/eval/{version}")
def eval(version:str):
    driver = init()
    records, summary, keys = driver.execute_query(
        "MATCH (:KubeVersion{kubernetesVersion:$version})-[:Contains]->(p) return p.NAME, p.INSTALLED, p.`FIXED-IN`, p.TYPE, p.VULNERABILITY, p.SEVERITY",
        {"version":version},routing = RoutingControl.READ, database = "neo4j"
    )
    driver.close()
    return records

@app.get("/rec/{version}")
def rec(version:str):
    driver = init()
    records, summary, keys = driver.execute_query(
        "MATCH (:KubeVersion{kubernetesVersion:$version})-[:Contains]->(p) return p.SEVERITY",
        {"version":version},routing = RoutingControl.READ, database = "neo4j"
    )
    driver.close()
    return records

@app.get("/vul/{code}")
def vul(code:str):
    driver = init()
    records, summary, keys = driver.execute_query(
        "MATCH (Vulnerability{VULNERABILITY:$CVE})<-[:Contains]-(p) return p.kubernetesVersion, p.`Date-Time`",
        {"CVE":code},routing = RoutingControl.READ, database = "neo4j"
    )
    driver.close()
    return records 