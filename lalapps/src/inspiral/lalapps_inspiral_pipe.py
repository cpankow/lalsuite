"""
inspiral_pipeline.py - standalone inspiral pipeline driver script

This script produced the necessary condor submit and dag files to run
the standalone inspiral code on LIGO data
"""

__author__ = 'Duncan Brown <duncan@gravity.phys.uwm.edu>'
__date__ = '$Date$'
__version__ = '$Revision$'

# import standard modules
import sys, os
import getopt, re, string
import tempfile

# import the modules we need to build the pipeline
from glue import pipeline
from lalapps import inspiral

def usage():
  msg = """\
Usage: lalapps_inspiral_pipe [options]

  -h, --help               display this message
  -v, --version            print version information and exit
  -u, --user-tag TAG       tag the job with TAG (overrides value in ini file)

  -d, --datafind           run LSCdataFind to create frame cache files
  -t, --template-bank      run lalapps_tmpltbank to generate a template bank
  -i, --inspiral           run lalapps_inspiral on the first IFO
  -T, --triggered-bank     run lalapps_trigbank to generate a triggered bank
  -I, --triggered-inspiral run lalapps_inspiral on the second IFO
  -C, --coincidence        run lalapps_inca on the triggers from both IFOs

  -j, --injections FILE    add simulated inspirals from FILE

  -p, --playground-only    only create chunks that overlap with playground
  -P, --priority PRIO      run jobs with condor priority PRIO

  -f, --config-file FILE   use configuration file FILE
  -l, --log-path PATH      directory to write condor log file

  -x, --dax                write abstract DAX file
"""
  print >> sys.stderr, msg

# pasrse the command line options to figure out what we should do
shortop = "hvdtiTICpj:u:P:f:l:x"
longop = [
  "help",
  "version",
  "datafind",
  "template-bank",
  "inspiral",
  "triggered-bank",
  "triggered-inspiral",
  "coincidence",
  "injections=",
  "playground-only",
  "user-tag=",
  "priority=",
  "config-file=",
  "log-path=",
  "dax"
  ]

try:
  opts, args = getopt.getopt(sys.argv[1:], shortop, longop)
except getopt.GetoptError:
  usage()
  sys.exit(1)

config_file = None
do_datafind = None
do_tmpltbank = None
do_inspiral = None
do_trigbank = None
do_triginsp = None
do_coinc = None
inj_file = None
usertag = None
playground_only = 0
condor_prio = None
config_file = None
log_path = None
dax = False

for o, a in opts:
  if o in ("-v", "--version"):
    print "$Id$"
    sys.exit(0)
  elif o in ("-h", "--help"):
    usage()
    sys.exit(0)
  elif o in ("-d", "--datafind"):
    do_datafind = 1
  elif o in ("-t", "--template-bank"):
    do_tmpltbank = 1
  elif o in ("-i", "--inspiral"):
    do_inspiral = 1
  elif o in ("-T", "--triggered-bank"):
    do_trigbank = 1
  elif o in ("-I", "--triggered-inspiral"):
    do_triginsp = 1
  elif o in ("-C", "--coincidence"):
    do_coinc = 1
  elif o in ("-j", "--injections"):
    inj_file = a
  elif o in ("-u", "--user-tag"):
    usertag = a
  elif o in ("-p", "--playground-only"):
    playground_only = 2
  elif o in ("-P", "--priority"):
    condor_prio = a
  elif o in ("-f", "--config-file"):
    config_file = a
  elif o in ("-l", "--log-path"):
    log_path = a
  elif o in ("-x", "--dax"): 	 
    dax = True
  else:
    print >> sys.stderr, "Unknown option:", o
    usage()
    sys.exit(1)

if not config_file:
  print >> sys.stderr, "No configuration file specified."
  print >> sys.stderr, "Use --config-file FILE to specify location."
  sys.exit(1)

if not log_path:
  print >> sys.stderr, "No log file path specified."
  print >> sys.stderr, "Use --log-path PATH to specify a location."
  sys.exit(1)

# try and make a directory to store the cache files and job logs
try: os.mkdir('cache')
except: pass
try: os.mkdir('logs')
except: pass

# create the config parser object and read in the ini file
cp = pipeline.DeepCopyableConfigParser()
cp.read(config_file)

# if a usertag has been specified, override the config file
if usertag:
  cp.set('pipeline','user-tag',usertag)
else:
  try:
    usertag = string.strip(cp.get('pipeline','user-tag'))
  except:
    usertag = None

# create a log file that the Condor jobs will write to
basename = re.sub(r'\.ini',r'',config_file)
tempfile.tempdir = log_path
if usertag:
  tempfile.template = basename + '.' + usertag + '.dag.log.'
else:
  tempfile.template = basename + '.dag.log.'
logfile = tempfile.mktemp()
fh = open( logfile, "w" )
fh.close()

# create the DAG writing the log to the specified directory
dag = pipeline.CondorDAG(logfile,dax)
if usertag:
  dag.set_dag_file(basename + '.' + usertag)
else:
  dag.set_dag_file(basename)

# create the Condor jobs that will be used in the DAG
df_job = pipeline.LSCDataFindJob('cache','logs',cp,dax)
tmplt_job = inspiral.TmpltBankJob(cp,dax)
insp_job = inspiral.InspiralJob(cp,dax)
trig_job = inspiral.TrigbankJob(cp)
inca_job = inspiral.IncaJob(cp)

# set better submit file names than the default
if usertag:
  subsuffix = '.' + usertag + '.sub'
else:
  subsuffix = '.sub'
df_job.set_sub_file( basename + '.datafind'+ subsuffix )
tmplt_job.set_sub_file( basename + '.tmpltbank' + subsuffix )
insp_job.set_sub_file( basename + '.inspiral' + subsuffix )
trig_job.set_sub_file( basename + '.trigbank' + subsuffix )
inca_job.set_sub_file( basename + '.inca' + subsuffix )

# set the usertag in the jobs
if usertag:
  tmplt_job.add_opt('user-tag',usertag)
  insp_job.add_opt('user-tag',usertag)
  trig_job.add_opt('user-tag',usertag)
  inca_job.add_opt('user-tag',usertag)

# add the injections
if inj_file:
  insp_job.add_opt('injection-file',inj_file)

# set the condor job priority
if condor_prio:
  df_job.add_condor_cmd('priority',condor_prio)
  tmplt_job.add_condor_cmd('priority',condor_prio)
  insp_job.add_condor_cmd('priority',condor_prio)
  trig_job.add_condor_cmd('priority',condor_prio)
  inca_job.add_condor_cmd('priority',condor_prio)

# see if we are using calibrated data
calibrated = False
for opt in cp.options('data'):
  if (opt.find('calibrated') >-1):
    calibrated = True

# get the pad and chunk lengths from the values in the ini file
pad = int(cp.get('data', 'pad-data'))
n = int(cp.get('data', 'segment-length'))
s = int(cp.get('data', 'number-of-segments'))
r = int(cp.get('data', 'sample-rate'))
o = int(cp.get('inspiral', 'segment-overlap'))
length = ( n * s - ( s - 1 ) * o ) / r
overlap = o / r

# read science segs that are greater or equal to a chunk from the input file
data = pipeline.ScienceData()
data.read(cp.get('input','segments'),length + 2*pad)

# create the chunks from the science segments
data.make_chunks(length,overlap,playground_only,0,overlap/2,pad)
data.make_chunks_from_unused(
  length,overlap/2,playground_only,overlap/2,0,overlap/2,pad)

# get the order of the ifos to filter
ifo1 = cp.get('pipeline','ifo1')
ifo2 = cp.get('pipeline','ifo2')
ifo1_snr = cp.get('pipeline','ifo1-snr-threshold')
ifo2_snr = cp.get('pipeline','ifo2-snr-threshold')
ifo1_chisq = cp.get('pipeline','ifo1-chisq-threshold')
ifo2_chisq = cp.get('pipeline','ifo2-chisq-threshold')

# create all the LSCdataFind jobs to run in sequence
prev_df1 = None
prev_df2 = None
first_df2 = None

# create a list to store the inspiral jobs
insp_nodes = []

# help pegasus plan jobs which use the same data on the same pool
group = 0

for seg in data:
  # find all the data
  df1 = pipeline.LSCDataFindNode(df_job)
  df1.set_start(seg.start() - pad)
  df1.set_end(seg.end() + pad)
  df1.set_observatory(ifo1[0])
  if prev_df1: 
    df1.add_parent(prev_df1)

  df2 = pipeline.LSCDataFindNode(df_job)
  if not first_df2:
    first_df2 = df2
  df2.set_start(seg.start() - pad)
  df2.set_end(seg.end() + pad)
  df2.set_observatory(ifo2[0])
  if prev_df2: 
    df2.add_parent(prev_df2)

  if do_datafind:
    dag.add_node(df1)
    if do_triginsp:
      dag.add_node(df2)

  prev_df1 = df1
  prev_df2 = df2

  seg_insp_nodes = []

  for chunk in seg:
    bank = inspiral.TmpltBankNode(tmplt_job)
    bank.set_start(chunk.start())
    bank.set_end(chunk.end())
    bank.set_ifo(ifo1)
    bank.set_cache(df1.get_output())
    if not calibrated: bank.calibration()
    bank.set_vds_group(group)

    if do_datafind: 
      bank.add_parent(df1)
    if do_tmpltbank: 
      dag.add_node(bank)

    insp1 = inspiral.InspiralNode(insp_job)
    insp1.set_start(chunk.start())
    insp1.set_end(chunk.end())
    insp1.add_var_opt('trig-start-time',chunk.trig_start())
    insp1.add_var_opt('trig-end-time',chunk.trig_end())
    insp1.add_var_opt('snr-threshold',ifo1_snr)
    insp1.add_var_opt('chisq-threshold',ifo1_chisq)
    insp1.set_ifo(ifo1)
    insp1.set_cache(df1.get_output())
    insp1.set_bank(bank.get_output())
    if not calibrated: insp1.calibration()
    insp1.set_vds_group(group)

    if do_tmpltbank:
      insp1.add_parent(bank)
    if not do_tmpltbank and do_datafind:
      insp1.add_parent(df1)
    if do_inspiral:
      dag.add_node(insp1)

    trigbank = inspiral.TrigbankNode(trig_job)
    trigbank.add_file_arg(insp1.get_output())
    trigbank.make_trigbank(chunk,0,ifo1,ifo2,usertag)
    trigbank.set_vds_group(group)

    if do_inspiral:
      trigbank.add_parent(insp1)
    if do_trigbank:
      dag.add_node(trigbank)

    insp2 = inspiral.InspiralNode(insp_job)
    insp2.set_start(chunk.start())
    insp2.set_end(chunk.end())
    insp2.set_ifo(ifo2)
    insp2.add_var_opt('snr-threshold',ifo2_snr)
    insp2.add_var_opt('chisq-threshold',ifo2_chisq)
    insp2.add_var_opt('trig-start-time',chunk.trig_start())
    insp2.add_var_opt('trig-end-time',chunk.trig_end())
    insp2.set_cache(df2.get_output())
    insp2.set_bank(trigbank.get_output())
    if not calibrated: insp2.calibration()

    if do_datafind:
      insp2.add_parent(df2)
    if do_trigbank:
      insp2.add_parent(trigbank)
    if do_triginsp:
      dag.add_node(insp2)

    # add the two inspiral jobs for this chunk to the stored list
    seg_insp_nodes.append(tuple([insp1,insp2]))

    # increment the group for each chunk
    group += 1

  # add the inspiral jobs for this segment to the list
  insp_nodes.append(seg_insp_nodes)

# now add the last df1 as a parent to the first df2 so we 
# don't have multiple datafinds running at the same time
if do_datafind:
  first_df2.add_parent(df1)
    
# now find coincidences between the two inspiral jobs
for i in range(len(data)):
  for j in range(len(data[i])):
    chunk = data[i][j]
    inca = inspiral.IncaNode(inca_job)
    # inca should work on the trigger start/end times to avoid duplicates
    if chunk.trig_start() > 0:
      inca.set_start(chunk.trig_start())
    else:
      inca.set_start(chunk.start() + overlap/2)
    inca.set_end(chunk.end() - overlap/2)
    inca.set_ifo_a(ifo1)
    inca.set_ifo_b(ifo2)
    
    # if there is a chunk before this one, add it to the job
    try: 
      data[i][j-1]
      inca.add_file_arg(insp_nodes[i][j-1][0].get_output())
      inca.add_file_arg(insp_nodes[i][j-1][1].get_output())
      if do_inspiral:
        inca.add_parent(insp_nodes[i][j-1][0])
      if do_triginsp:
        inca.add_parent(insp_nodes[i][j-1][1])
    except IndexError:
      pass

    # add this chunk to the job
    inca.add_file_arg(insp_nodes[i][j][0].get_output())
    inca.add_file_arg(insp_nodes[i][j][1].get_output())
    if do_inspiral:
      inca.add_parent(insp_nodes[i][j][0])
    if do_triginsp:
      inca.add_parent(insp_nodes[i][j][1])
    
    # if there is a chunk after this one, add it to the job
    try:
      data[i][j+1]
      inca.add_file_arg(insp_nodes[i][j+1][0].get_output())
      inca.add_file_arg(insp_nodes[i][j+1][1].get_output())
      if do_inspiral:
        inca.add_parent(insp_nodes[i][j+1][0])
      if do_triginsp:
        inca.add_parent(insp_nodes[i][j+1][1])
    except IndexError:
      pass
      
    if do_coinc:
      inca.get_output_a()
      inca.get_output_b()
      dag.add_node(inca)

# write out the DAG
dag.write_sub_files()
dag.write_dag()

# write a message telling the user that the DAG has been written
if dax: 	 
  print """\nCreated a DAX file which can be submitted to the Grid using 	 
Pegasus. See the page: 	 
  	 
  http://www.lsc-group.phys.uwm.edu/lscdatagrid/griphynligo/vds_howto.html 	 
  	 
for instructions.
"""
else:
  print "\nCreated a DAG file which can be submitted by executing"
  print "\n   condor_submit_dag", dag.get_dag_file()
  print """\nfrom a condor submit machine (e.g. hydra.phys.uwm.edu)\n
If you are running LSCdataFind jobs, do not forget to initialize your grid 
proxy certificate on the condor submit machine by running the commands

  unset X509_USER_PROXY
  grid-proxy-init -hours 72

Enter your pass phrase when promted. The proxy will be valid for 72 hours. 
If you expect the LSCdataFind jobs to take longer to complete, increase the
time specified in the -hours option to grid-proxy-init. You can check that 
the grid proxy has been sucessfully created by executing the command:

  grid-cert-info -all -file /tmp/x509up_u`id -u`

This will also give the expiry time of the proxy. You should also make sure
that the environment variable LSC_DATAFIND_SERVER is set the hostname and
optional port of server to query. For example on the UWM medusa cluster this
you should use

  export LSC_DATAFIND_SERVER=dataserver.phys.uwm.edu

Contact the administrator of your cluster to find the hostname and port of the
LSCdataFind server.
"""

# write out a log file for this script
if usertag:
  log_fh = open(basename + '.pipeline.' + usertag + '.log', 'w')
else:
  log_fh = open(basename + '.pipeline.log', 'w')
  
# FIXME: the following code uses obsolete CVS ID tags.
# It should be modified to use git version information.
log_fh.write( "$Id$" + "\n\n" )
log_fh.write( "Invoked with arguments:\n" )
for o, a in opts:
  log_fh.write( o + ' ' + a + '\n' )
log_fh.write( "\n" )
log_fh.write( "Parsed " + str(len(data)) + " science segments\n" )
total_data = 0
for seg in data:
  for chunk in seg:
    total_data += len(chunk)
print >> log_fh, "total data =", total_data

print >> log_fh, "\n===========================================\n"
print >> log_fh, data
for seg in data:
  print >> log_fh, seg
  for chunk in seg:
    print >> log_fh, chunk

sys.exit(0)

