/* double inclusion protection */
#ifndef XLALPSSINTERFACE_H
#define XLALPSSINTERFACE_H

/* PSS has some strange internal dependencies between its headers,
   better don't change the following order */
#include <stdio.h>
#include "pss_math.h"
#include "pss_sfc.h"
#include "pss_snag.h"
#include "pss_sfdb.h"

#include <lal/LALDatatypes.h>

/* PSS interface datatypes based on PSS datatypes */
typedef GD           PSSTimeseries;
typedef EVEN_PARAM   PSSEventParams;
typedef HEADER_PARAM PSSHeaderParams;

/* creator & destructor functions */
extern PSSEventParams *XLALCreatePSSEventParams(UINT4 length);
extern PSSTimeseries  *XLALCreatePSSTimeseries(UINT4 length);
extern void XLALDestroyPSSTimeseries(PSSTimeseries *ts);
extern void XLALDestroyPSSEventParams(PSSEventParams *ts);

/* LAL <-> PSS timeseries conversion functions */
extern REAL8TimeSeries
*XLALConvertPSSTimeseriesToREAL8Timeseries
(REAL8TimeSeries *ts,
 PSSTimeseries *tsPSS);
extern PSSTimeseries
*XLALConvertREAL8TimeseriesToPSSTimeseries
(PSSTimeseries *tsPSS,
 REAL8TimeSeries *ts);

extern REAL4TimeSeries
*XLALConvertPSSTimeseriesToREAL4Timeseries
(REAL4TimeSeries *ts,
 PSSTimeseries *tsPSS);
extern PSSTimeseries
*XLALConvertREAL4TimeseriesToPSSTimeseries
(PSSTimeseries *tsPSS,
 REAL4TimeSeries *ts);

/* functions for time domain cleaning */
extern PSSTimeseries
*XLALPSSHighpassData
(PSSTimeseries *tsout,
 PSSTimeseries *tsin,
 PSSHeaderParams* hp,
 REAL4 f);
extern PSSEventParams
*XLALIdentifyPSSCleaningEvents
(PSSEventParams *events,
 PSSTimeseries *ts,
 PSSHeaderParams* hp);
extern PSSTimeseries
*XLALSubstractPSSCleaningEvents
(PSSTimeseries *tsout,
 PSSTimeseries *tsin,
 PSSTimeseries *tshp,
 PSSEventParams *events,
 PSSHeaderParams* hp);

#endif /* XLALPSSINTERFACE_H double inclusion protection */
