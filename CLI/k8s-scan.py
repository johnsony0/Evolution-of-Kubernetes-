#run this using 'python .\Neo4jCLI.py'
#pip install neo4j, pip install pandas
from neo4j import GraphDatabase, RoutingControl
import pandas as pd
import argparse

def isvalid(driver,version):
    valid_version = False
    records,summary,keys = driver.execute_query(
        "MATCH (p:KubeVersion) return p.kubernetesVersion",
        routing = RoutingControl.READ, database = "neo4j"
    )
    for record in records:
        if version == record['p.kubernetesVersion']:
            valid_version = True
    return valid_version


def dependencies(driver,version,list):
    #run cypher query 
    records,summary,keys = driver.execute_query(
        "MATCH (:KubeVersion{kubernetesVersion:$version})-[:Contains]->(p) return p.dependencyName,p.dependencyVersion",
        {"version":version}, routing = RoutingControl.READ, database = "neo4j"
    )
    #print dependencies data
    print("total dependencies in version",version,"is",len(records))
    #print list of dependencies if user requests it
    if(list == 'some'):
        df = pd.DataFrame(records,columns=['dependency name','dependency version'])
        print(df)
    elif (list == 'all'):
        df = pd.DataFrame(records,columns=['dependency name','dependency version'])
        with pd.option_context('display.max_rows',None):
            print(df)

def compare(driver,version_1,version_2,list):
    #separate based on if both version + name is same, name is same different version, both are different
    records_1,summary,keys = driver.execute_query(
        "MATCH (:KubeVersion{kubernetesVersion:$version})-[:Contains]->(p) return p.dependencyName, p.dependencyVersion",
        {"version":version_1}, routing = RoutingControl.READ, database = "neo4j"
    )
    records_2,summary,keys = driver.execute_query(
        "MATCH (:KubeVersion{kubernetesVersion:$version})-[:Contains]->(p) return p.dependencyName, p.dependencyVersion",
        {"version":version_2}, routing = RoutingControl.READ, database = "neo4j"
    )

    #convert records into a pandas dataframe
    df_1 = pd.DataFrame(records_1,columns=['dependency name','dependency version'])
    df_2 = pd.DataFrame(records_2,columns=['dependency name','dependency version'])
    #create dataframe with exact same dependencies
    df_same = pd.merge(df_1,df_2,how='inner',on=['dependency name','dependency version'])
    
    #delete all entries that are exactly the same dependencies
    df_1 = pd.concat([df_1,df_same],ignore_index=True)
    df_2 = pd.concat([df_2,df_same],ignore_index=True)
    df_1.drop_duplicates(keep=False,ignore_index=True,inplace=True)
    df_2.drop_duplicates(keep=False,ignore_index=True,inplace=True)

    #create dataframe with updated dependencies 
    df_updated = pd.merge(df_1,df_2,how='inner',on=['dependency name'])
    df_updated.rename(columns={"dependency version_x":"dependency version_1","dependency version_y":"dependency version_2"},inplace=True)
    
    #delete all entries that are updated dependencies
    df_1.rename(columns={"dependency version":"dependency version_1"},inplace=True)
    df_2.rename(columns={"dependency version":"dependency version_2"},inplace=True)
    df_1 = pd.concat([df_1,df_updated],join='inner',ignore_index=True)
    df_2 = pd.concat([df_2,df_updated],join='inner',ignore_index=True)
    df_1.drop_duplicates(keep=False,ignore_index=True,inplace=True)
    df_2.drop_duplicates(keep=False,ignore_index=True,inplace=True)
    
    print("number of dependencies that has remained the same is:",len(df_same))
    print("number of dependencies that has been updated is:", len(df_updated))
    print("number of dependencies that has been removed is:", len(df_2))
    print("number of dependencies that has been added is:", len(df_1))
    if(list == 'some'):
        print(df_same)
        print(df_updated)
        print(df_1)
        print(df_2)
    elif (list == 'all'):
        with pd.option_context('display.max_rows',None):
            print(df_same)
            print(df_updated)
            print(df_1)
            print(df_2)


def main():
    #login to neo4j
    uri = "neo4j+s://df706296.databases.neo4j.io"
    username = "neo4j"
    password = "6cJ80Ld1ImFnjbROGGGUeoHNootL7_zHv6aBpqdNHDA"
    driver = GraphDatabase.driver(uri, auth=(username, password))

    #argument parser for CLI
    parser = argparse.ArgumentParser(description="Tool to analyze vulnerabilities in dependencies of Kubernetes")
    parser.add_argument("version",metavar="V",type=str,help="version of Kubernetes you would like to scan")
    parser.add_argument("version_",metavar="V_",nargs='?',type=str,help="second version of Kubernetes, required for comparisons else leave empty")
    parser.add_argument("-d","--dependencies",action="store_true",help="list all dependencies of select version")
    parser.add_argument("-c","--compare",action="store_true",help="compare dependencies of two chosen versions")
    parser.add_argument("-e","--evaluate",action="store_true",help="evaluate security posture of chosen version")
    parser.add_argument("-r","--recommend",action="store_true",help="choose next version with less or equal vulnerabilities")
    parser.add_argument("-a","--analyze",action="store_true",help="analyze all versions released up till selected version")
    parser.add_argument("-l","--list",default='some', choices=['none','some','all'],required=False,help="[default = some] toggle whether to list all data or not")
    args = parser.parse_args()

    #check if version is valid
    if not(isvalid(driver,args.version)):
        parser.error('Invalid version entered, refer to list of valid entries or -h for help')
    
    #check if any function is called, if not return error
    if not (args.dependencies or args.evaluate or args.recommend or args.analyze or args.compare):
        parser.error('No action requested, add -h for help')

    #do function based on input
    if(args.dependencies):
        dependencies(driver,args.version,args.list)
    if(args.compare):
        #checks if second argument is none or invalid, gives proper response to error
        if (args.version_ == None):
            parser.error('Second version entry is not defined, add -h for help')
        elif not(isvalid(driver,args.version_)):
            parser.error('Invalid second version entered, refer to list of valid entries of -h for help')
        compare(driver,args.version,args.version_,args.list)
    driver.close()
    
if __name__ == "__main__":
    main()


"""
uri = "neo4j+s://df706296.databases.neo4j.io"
    username = "neo4j"
    password = "6cJ80Ld1ImFnjbROGGGUeoHNootL7_zHv6aBpqdNHDA"
    driver = GraphDatabase.driver(uri, auth=(username, password))

    driver.close()


//visualize all nodes from one version of kubernetes
MATCH p=(:KubeVersion{kubernetesVersion:"kubernetes-1.29.0-alpha.1"})-[:Contains]->() return p;

//visualize all nodes from two versions of kubernetes
MATCH p=(:KubeVersion{kubernetesVersion:"kubernetes-1.29.0-alpha.1"})-[:Contains]->() 
return p AS a
UNION ALL MATCH p=(:KubeVersion{kubernetesVersion:"kubernetes-1.28.2"})-[:Contains]->()
return p AS a

//list of all dependencies name and version from one version of Kubernetes
MATCH (:KubeVersion{kubernetesVersion:"kubernetes-1.29.0-alpha.1"})-[:Contains]->(p) return p.dependencyVersion,p.dependencyName;

//visualize all versions of kubernetes and their dependencies and relations
MATCH p=()-[:Contains]->() RETURN p;

//list and visualize all versions of kubernetes
MATCH (p:KubeVersion) return p

def run_cypher_query(driver,query):
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            print(record)
"""


