import xmlutils
import data_types
import warnings
import numpy as np
import matplotlib.pyplot as plt
import re
from constraints import Constraint
from numpy.random import random_sample

c = 299792.458

model_classes = {"absorbers":"Absorber","continuum_points":"ContinuumPoint","regions":"Region"}

atomic_data=data_types.SpectralLine.get_lines()

class Model(object): 
    def __init__(self, **kwargs):
        """
        inputs:
        -------
        absorbers: list(data_types.Absorber)  is a list of absorber references 
        """ 
        self.model_id=''
        self.parse_kwargs(**kwargs)

        if self.xmlfile==None:
            try:
                self.xmlfile=self.absorbers[0].xmlfile.name
            except:
                raise Exception("must specify either xml filename or model data")

        self.xml_fit = xmlutils.Dudexml(self.xmlfile)

        if not all(x in kwargs.keys() for x in ["absorbers", "continuum_points", "regions"]):
            if self.xmlfile:
                self.get_model()
            else:
                raise Exception("need to define at least one argument")
        
        for attr in ["chi2","pixels","params"]:
            try:
                assert(attr in kwargs.keys())
            except AssertionError:
                setattr(self,item,0.)
                warnings.warn("%s wasn't defined.  setting to 0."%(item))
        self.locked = {}
        self.count_params()

    def __eq__(self,other):
        for item in ['model_id','chi2','pixels','params','locked','absorbers']:
            if getattr(self,item)!=getattr(other,item):
                return False
        return True
    
    def __neq__(self,other):
        return not self.__eq__(other)


    def __str__(self):
        """
        string output for a model will be like:
    
        model_id=HI N=17.12345 b=12.345678 z=1.234567890
        model_id=SiI N=11.12345 b=12.345678 z=1.234567890
        model_id=OI N=11.12345 b=12.345678 z=1.234567890
        locked=OI:bLocked HI:zLocked
        chi2=123.4 pixels=154

        """
        string = "--------continuum points--------\n"
        for item in self.continuum_points:
            string+=str(item)+"\n"

        locked = {}
        string = "-----------absorbers------------\n"
        for item in self.absorbers:
            string+=str(item)+"\n"
            for param in ['NLocked','bLocked','zLocked']:
                if getattr(item,param):
                    locked[item.absorber_id] = param
        string+="locked="
        for key, val in locked.items():
            if val:
                string+=str(key)+":"+str(val)+" "
        string+="\nchi2=%lf pixels=%lf params=%lf\n\n"%(float(self.chi2),float(self.pixels),float(self.params))
        return string

    def append(self,inst=None,tag=None,**kwargs):
        if not tag: tag=kwargs.get("tag")
        if not tag: raise Exception("must specify data type")
        if tag in model_classes.values(): tag= inv_dict(tag)
        if inst:
            getattr(self,tag).append(inst)
            
        else:
            getattr(self,tag).append(data_types.Data.factory(**kwargs))

    def consolidate_regions(self):
        self.regions = data_types.Region.consolidate_regions(self.regions)
        self.write()

    def count_params(self):
        """get the number of params being optimized"""
        params=0
        for ab in self.absorbers:
            if ab.in_region(self.regions):
                for lock in ["bLocked","zLocked","NLocked"]:
                    if getattr(ab,lock)==True:
                        params+=1
        self.params = params

    def get(self,id,tag,param=None):
        if tag in model_classes.values(): tag= inv_dict(tag)
        for item in getattr(self,tag):
            if id==item.id:
                if param:
                    try:
                        return float(getattr(item,param))
                    except:
                        return getattr(item,param)
                else:
                    return item
        raise Exception("item not found: %s"%(id))
        
    def get_model(self,**kwargs):
        """get all model data from xml and set attribs for self"""
        for key, val in model_classes.items():
            lst=[]
            for item in self.xml_fit.get_node_list(val):
                assert(item.tag==val)
                inp = {"xmlfile":self.xml_fit.name,"node":item,"tag":item.tag}
                if item.tag=="Absorber":  #append atomic data if absorber
                    inp["atomic_data"]=atomic_data
                lst.append(data_types.Data.factory(**inp))
            if len(lst)>0:
                setattr(self,key,lst)
            else:
                setattr(self,key,None)
        self.parse_kwargs(**kwargs)
        self.test_chi2()

    def monte_carlo_set(self,id,tag,param,val_range):
        """set a param for Data `id` to a random value in val_range"""
        a=float(val_range[0])
        b=float(val_range[1])
        new = (b-a)*random_sample()+a
        self.set_val(id,tag,**{param:new})

    def parse_kwargs(self,**kwargs):
        for key, val in kwargs.items():
            try:
                setattr(self,key,float(val))
            except:
                setattr(self,key,val)
        self.test_chi2()

    def parse_node(self,node):
        dat = self.xml.get_node_data(node=node)
        parse_kwargs(self,**dat)

    def pop(self,key,tag):
        if tag in model_classes.values(): tag=inv_dict(tag)
        if type(key) == str:
            return self._pop_by_id(key,tag)
        elif type(key) == int:
            return self._pop_by_index(key,tag)
        else:
            lst = getattr(self,tag)
            for i in len(lst):
                if lst[i]==key:
                    ret = lst.pop(i)
                    setattr(self,tag,lst)
                    return ret
        raise Exception("item not found: %s"%(str(key)))

    def _pop_by_id(self,key,tag):
        lst = getattr(self,tag)
        for i in range(len(lst)):
            if lst[i].id==key:
                ret = lst.pop(i)
                setattr(self,tag,lst)
                return ret

    def _pop_by_index(self,i,tag):
        ret = getattr(self,tag).pop(i)
        setattr(self,tag,getattr(self,tag))
        return ret

    def set_val(self,id,tag,**kwargs):
        """set the values of a given data element"""
        if tag in model_classes.values(): tag=inv_dict(tag)
        for item in getattr(self,tag):
            if item.id==id:
                item.set_data(**kwargs)
                print("setting to %s"%(str(kwargs)))
        self.xml_fit.write()

    def test_chi2(self):
        for item in ["chi2", "pixels", "params"]:
            try:
                float(getattr(self,item))
            except:
                if item=="params":
                    self.params()
                else:
                    warnings.warn(item+" not present...")
                    setattr(self,item,0.)
            
    def write(self):
        for item in self.lst:
            #get the node
            node=xmlutils.Dudexml.get_node(item.id,item.tag)
            for key in node.attrib.keys():
                node.set(key, str(item.key))
        xmlutils.Dudexml.write()


class ModelDB(object):
    def __init__(self, name=None, models=[], constraints=None,**kwargs): 
        """
        Model Database

        Inputs:
        -------
        models:  list of Model instances
        constraints: dict of dicts of tuples of floats.  (see ModelDB.constrain) 
        name: name of the xml models file.  (not the fit file)
        """

        for key, val in dict(kwargs).items():
            setattr(self,key,val)

        self.name=name
        self.dbxml=xmlutils.Model_xml(filename=name)
        if len(models)>0:
            self.lst = models
            self.root=self.create(str(name))
        elif name:   
            self.lst = ModelDB.read(str(name), return_db=False)
            self.root=self.dbxml.read(name)
        else:
            self.lst = []

        if constraints:
            self.lst = ModelDB.constrain(self,constraints)

    def append(self, model):
        self.lst.append(model)

    def best_fit(self,id,param,order,xmin=None,xmax=None, plot=True, constraints=None):
        """
        get a best fit of data with respect to `param'

        id: id of absorber
        param:  parameter name (N,b,z)
        order:  order of polynomial to fit
        xmax, xmin: range of values to consider
        locked:  get only locked parameters?
        plot:   plot the data?  otherwise return function, x, y
        """
        x = []
        y = []

        if constraints!=None:
            lst=ModelDB.constrain(self,constraints)
            if len(lst)==0:
                raise Exception("no surviving models:\n%s"%(str(constraints)))
            if len(lst)==len(self.lst):
                warnings.warn("everything passed")
        else:
            lst = self.lst
    
        for item in lst:
            ab = item.get(id,"Absorber")
            if ab.locked(param):
                x.append(float(getattr(ab,param)))
                y.append(float(item.chi2))

        if len(x)==0 or len(y)==0 or len(x)!=len(y):
            raise Exception("ill condittioned input: \n  x=%s\n  y=%s"%(str(x),str(y)))

        if xmin==None and xmax==None:
            xmax = max(x)
            xmin = min(x)

        x=np.array(x)
        y=np.array(y)

        coeffs=np.polyfit(x-x.mean(),y,int(order))
        f = np.poly1d(coeffs)
        if plot:
            xx = np.arange(xmin,xmax, np.abs(xmax-xmin)/100.)
            yy = f(xx-x.mean())
            plt.xlim(xmin,xmax)
            plt.plot(xx,yy,'b-')
            plt.plot(x,y,'ro')
            plt.show()
        return f, x, y


    @staticmethod
    def constrain(obj,constraints):
        """
        example constraints:   
            constraints={"chi2":123,"params":3,"pixels":2345,"D":{"N":(12.3,14.3),"b":(15,16)}}
        """
        constraint=Constraint(**constraints)
        return [item for item in obj.lst if constraint.compare(item)]

    def create(self,filename):
        """create an xml file file structure.  returns root"""
        import xml.etree.ElementTree as et
        import datetime
        now = str(datetime.datetime.now())
        root = et.Element('modeldb')

        #set up header data
        head = et.SubElement(root, 'head')
        title = et.SubElement(head, 'title')
        title.text = 'Fitting Models'
        created = et.SubElement(head, 'dateCreated')
        created.text = now
        modified = et.SubElement(head, 'dateModified')
        modified.text = now

        models = et.SubElement(root, 'models')

        #load the model db
        for item in self.lst:
            current_group = None
            group_name = item.model_id 
            if current_group is None or group_name != current_group.text:
                current_group = et.SubElement(root, 'model', {'model_id':group_name,'xmlfile':item.xmlfile,'chi2':str(item.chi2),'pixels':str(item.pixels),'params':str(item.params)})

            children = []

            for att in model_classes.keys():
                if getattr(item,att) != None:
                    children+=[it.node for it in getattr(item,att)]
            if len(children)==0:
                raise Exception("no children are present")
            current_group.extend(children)
        return root

    def get(self,xmlfile,chi2,pixels,params):
        self.lst.append(Model(xmlfile=xmlfile,chi2=chi2,pixels=pixels,params=params))

    def get_best_lst(self, id=None, param=None):
        """
        gets best fit.

        if `param' is specified, then gets best fit with a given parameter locked.
        param should be either bLocked, zLocked or NLocked
        """
        if not param is None:
            self.lst=sorted(self.lst, key=lambda x: x.chi2)
            return [(mod, mod.chi2) for mod in self.lst]
        else:
            return self.get_locked(id, param)  #already sorted

    def get_err(self, id, param_name):
        """get 1 sigma error from chi2 = chi2min + 1

        param_name is in [N,b,z]

        """
        tmp = self.get_best_lst(param=param_name+'Locked')
        lst = [item[0] for item in tmp]
        chi2 = [item[1] for item in tmp]
        chi2min = float(chi2[0])
        onesig=[]
        for item in lst:
            if item.chi2<chi2min+1.:
                onesig.append(getattr(item.getabs(id),param_name))
        return getattr(lst[0].getabs(id),param_name) ,max(onesig), min(onesig)

    def get_locked(self, id, tag, param):
        tmp = []
       
        for mod in self.lst:
            try:
                if to_bool(mod.get(id,tag,param+"Locked")):
                    tmp.append(mod)
            except:
                pass
        tmp =  sorted(tmp, key=lambda x: x.chi2)
        return [(mod.get(id,tag,param), mod.chi2) for mod in tmp]

    def get_min_chi2(self):
        return np.amin(np.array([item.chi2 for item in self.lst]))

    def get_model(self, id):
        for item in self.lst:
            if item.id==id: 
                return item

    def get_vel_shift(self,id1,id2):
        return [item.get_vel(id1,id2) for item in self.lst]

    def grab(self,xmlfile,chi2,pixels,params,**kwargs):
        """grab from xml file"""
        #need to reinstantiate xml file
        mod = Model(xmlfile=xmlfile,chi2=chi2,pixels=pixels,params=params,**kwargs)
        self.lst.append(mod)
        return
        
    def merge(self,other):
        self.lst += other.lst

    def parse_kwargs(self,**kwargs):
        for key, val in kwargs.items():
            try:
                setattr(self,key,float(val))
            except:
                setattr(self,key,val)

    def pop(self,i):
        return self.lst.pop(i)
    
    @staticmethod 
    def read(filename,return_db=True):
        """read from xml, return inputs for Model"""
        root=xmlutils.Model_xml.get_root(filename)
        models = root.findall('model') 
        if len(models)==0:
            raise Exception("no models saved")
        model_list = []
        for model in models:
            
            kwargs={}
            for key, val in model_classes.items():
                tmplst=[]
                for item in model.findall(val):
                    assert(item.tag==val)
                    inp = {"node":item,"tag":item.tag}
                    if val=="Absorber": 
                        inp["atomic_data"]=atomic_data
                    tmplst.append(data_types.Data.factory(**inp))
                if len(tmplst)>0:
                    kwargs[key]=tmplst
            for key, val in model.attrib.items():
                kwargs[key] = val
            model_list.append(Model(**kwargs))
        db = ModelDB(filename, models=model_list)
        if return_db:
            return db
        else:
            return db.lst

    def set_val(self,id,**kwargs):
        """set the values of a given data element"""
        new = self.lst.pop(id)
        new.set_val(**kwargs)
        self.lst.append(new)

    def write(self,filename=None):
        if filename==None:
            filename=self.name 
        root = self.create(filename)
        self.dbxml.write(filename,root)

#    some helper functions:
#------------------------------
 
def inv_dict(tag, dic=model_classes):
    if tag in dic.values():
        tmp = {v:k for k, v in dic.items()} 
        return tmp[tag]

def to_bool(string):
    string = string.lower()
    if string=="true":
        return True
    else:
        return False
