from model import Model, ModelDB
import os
from os.path import split, isfile, join
import subprocess
import xml.etree.ElementTree as et
from wavelength import c
import spec_parser


def run_optimize(fname,step=False, verbose=False, method='dude',timeout=45):
    """
    call dude and run OptimizeXML from the command line.

    input:
    ------
    fname:  source dude xml file (string)
    step (bool): if True, calls dude's step-iteration procedure,
        dumping some number of fits for each step of the procedure, named 
        \"iteration_%d.xml\"

    ouput:
    ------
    popt, pcov:   if method!= 'dude', outputs optimized parameters and 
                  covariance matrix (tuple)

    Raises:
    -------
    None
    """
    if method=='dude':
        #call dude from the command line and call its Levenberg-marquardt algo.
        commands=["java","-cp",
                  "/home/scott/programming/dude/jd/build", 
                  "dude.commandline.OptimizeXML", 
                  fname
                  ]
        if step:
            commands.append('step')
        if verbose:
            print("running: %s"%(" ".join(commands)))
        subprocess.call(commands,timeout=timeout)
    else: #use code from this project
        raise Exception("doesn't yet work as of 2016-02-29")
        model=model.Model(xmlfile=fname)
        src_data=model.flux
        popt, pcov = optimizer.optimize(src_data, model)
        return popt,pcov

def newdb(xmlfile,dbfile=None,params=None,**kwargs):
    """get a model, append to new database"""
    model = Model(xmlfile=xmlfile)
    return ModelDB(dbfile,[model],**kwargs)

def get_model(xmlfile,chi2=0.,pixels=0.):
    """
    get a single model instance from an xmlfile.  This exists just to provide 
    multiple points of entry to get a model

    Input:
    ------
    xmlfile : a dude xml fit file
    chi2 : chi-square.  default=0.
    pixels : number of pixels being optimized.  default=0

    Output:d
    -------
    model.Model instance 

    """
    return Model(xmlfile=xmlfile,chi2=chi2,pixels=pixels)


def populate_database(abs_ids,keep=False,path=None,db=None,constraints=None):
    """
    parse all xmlfiles in a given directory and returns a ModelDB instance

    Input:
    ------
    path : specified path to check

    Output:
    -------
    ModelDB instance

    Raises:
    -------
    Exception

    """

    if type(abs_ids)!=list:
        raise Exception("abs_ids needs to be list")

    if len(abs_ids)==0:
        raise Exception("need at least one absorber specified.  abs_ids=[]")

    files=[]
    if not path:
        path=os.getcwd()
    for f in os.listdir(path):
        if split(f)[-1].startswith('iteration') and split(f)[-1].endswith(".xml"):
            files.append(f)

    if len(files)==0 and not db:
        raise Exception("too few files")

    models=[Model( xmlfile=join(path,f), abs_ids=abs_ids ) for f in files]

    if bool(db): #if None or []
        if type(db) is str:
            db=load_from_db(db)
        db.append_lst(models,constraints=constraints)
    else:
        db = ModelDB(models=models,constraints=constraints)

    if not keep:
        for f in files:
            os.remove(join(path,f))
    return db


def append_db(db,abs_ids,keep=False,path=None,constraints=None):
    """populate existing database"""
    populate_database(abs_ids,keep=keep,path=path,db=db,constraints=constraints)

   
def load_from_db(dbxml):
    """alias to load a database"""
    return ModelDB.read(dbxml)

def get_db(dbfile):
    """alias to load a database"""
    return ModelDB.read(dbfile)

def random(xmlfile,itemid,tag,param,val_range,modelid=None):
    """get a new random setting a parameter to a random value in val_range (tuple or list)"""
    mod=Model(xmlfile=xmlfile,chi2=0,pixels=0,params=0,id=modelid)
    old = mod.get_datum(itemid,tag,"N")
    mod.monte_carlo_set(itemid,tag,param,val_range)
    new=mod.get_datum(itemid,tag,"N")
    assert(old!=new)
    print("model written to %s"%(xmlfile))

def all_conts(db=None):
    """get the set of all continua"""
    if type(db) is str:
        db = load_from_db(db)
    elif db is None: 
        db = load_from_db('database.xml')
    conts=[]
    for item in db:
        conts.append((item.ContinuumPointList, item.xmlfile))
    return list(set(conts))

def cont_check_pipeline(reduced_chi2_limit=1.8,verbose=True, db=None):
    if type(db) is str:
        db = load_from_db(db)
    conts = all_conts(db)

    ids = [item[0] for item in conts]
    for item in ids:
        assert(ids.count(item)==1)
    out=[]  #the 'good' continua
    for item in conts:
        models = db.get_lst_from_id(id=item[0],attr='ContinuumPointList')
        _min = min([float(mod.reduced_chi2) for mod in models])
        _min_chi2=min([float(mod.chi2) for mod in models])
        if _min <= reduced_chi2_limit:
            out.append((item[0],item[1],_min,_min_chi2))
    if verbose:
        print(len(out))
        for item in out:
            msg="%15s, id=%15s: \n    reduced chi2 = %6.4f, chi2=%6.4f"%(item[0],item[1],item[2],item[3])
            print(msg)
        print('\n')
    return out

def getDH(vr=(-0.5,0.5), dbfile='database.xml'):
    import matplotlib.pyplot as plt

    db = load_from_db(dbfile) 
    allmods = []
    _conts = cont_check_pipeline(db=db)
    conts = [item[0] for item in _conts]
    for item in db:
        if vr[0]<=item.get_shift('D','H')<=vr[1] and item.ContinuumPointList in conts:
            allmods.append(item)

    for cont in _conts:
        id = cont[0]
        name=cont[1]
        mods = []
        for mod in db.models:
            if vr[0]<=mod.get_shift('D','H')<=vr[1] and mod.ContinuumPointList==id:
                mods.append(mod)

        #dh = [{'dh':item.dh, 'chi2':item.chi2} for item in mods]
        plt.plot([item.dh for item in mods], [item.reduced_chi2 for item in mods],'ko')
        plt.title(name)
        plt.show()
        

    plt.plot([item.dh for item in allmods], [item.chi2 for item in allmods],'ko')
    plt.title("all continua")
    plt.show()

def check_for_cont_duplicates():
    import datetime
    import os
    def print_pretty(lst):
        for item in lst:
            print("  %15s  %15s"%(item[0],item[1]))
    def get_new_name(name):
        name, ext = os.path.splitext(name)
        num = 1
        new_name = name+str(num)+ext
        while os.path.isfile(new_name):
            num+=1
            new_name=name+str(num)+ext
        return new_name

    db = load_from_db('database.xml')
    conts = all_conts(db)
    names = [item[1] for item in conts]
    duplicates = list(set([(item[0],item[1]) for item in conts if names.count(item[1]) > 1 ]))
    print_pretty(duplicates)
    
    #rewrite duplicates to different xmlfiles
    for item in duplicates:
        models = db.get_lst_from_id(id=item[0],attr='ContinuumPointList')
        models = sorted( models, key=lambda x: x.chi2 )
        best_fit = models[0]
        new_name = get_new_name(best_fit.xmlfile)
        for i in range(0,len(db.models)):  #update db
            if db[i] in models:
                db[i].xmlfile=new_name  #update for model
            
        best_fit.write(filename=new_name)
                
    #write changes.  to avoid overwriting potentially desirable data, append date, time to fname
    db.write(str(datetime.datetime.now().isoformat()+"_db.xml"))


def parse(filename, ab_ids, path='/home/scott/research/J0744+2059/'):
    """clear a db file of all absorbers not in ab_ids"""

    tree = et.parse(join(path,filename))

    root = tree.getroot()
    parent = root.find('AbsorberLists')
    models = root.find('ModelDB').findall('model')

    for ablist in parent.findall('AbsorberList'):
        for ab in ablist.findall('Absorber'):
            if ab.get('id') not in ab_ids:
                ablist.remove(ab)
        if len(list(ablist))==0:
            parent.remove(ablist)
    tree.write(join(path,filename))


if __name__=='__main__':
    #parse("FeIIdb.xml",["FeII", "FeII_1","FeII_2","FeII_3","FeII_4","FeII_5"])
    pass

    #import plot_distribution as plt
    """path="/home/scott/research/J0744+2059/"
    fname="test.xml"
    abs_ids=["CIV_1","CIV_2","CIV_3"]
    model=Model(xmlfile=os.path.join(path,fname))
    db=random_sampling(model,"CIV_3","N",[13.2,13.7],4,abs_ids,constraints={},iden2=None)
    print("len db: %d"%(len(db)))
    for item in db:
        print(item.chi2, item.get_datum("CIV_3","Absorber","N"))"""
        
    #db=load_from_db("testdb.xml")
    #db=populate_database(abs_ids=["CIV_1","CIV_2","CIV_3"],path=path)
    #db.write("testdb.xml")
    #plt.plot_chi2(db,"N",xlabel="N column", iden="test")

        
    
    
    
