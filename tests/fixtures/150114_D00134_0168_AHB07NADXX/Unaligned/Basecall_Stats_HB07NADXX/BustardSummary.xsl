<?xml version="1.0"?> 
<!--
Copyright (c) 2007-2009 Illumina, Inc.

This software is covered by the "Illumina Genome Analyzer Software
License Agreement" and the "Illumina Source Code License Agreement",
and certain third party copyright/licenses, and any user of this
source file is bound by the terms therein (see accompanying files
Illumina_Genome_Analyzer_Software_License_Agreement.pdf and
Illumina_Source_Code_License_Agreement.pdf and third party
copyright/license notices).

This file is part of the Consensus Assessment of Sequence And VAriation
(CASAVA) software package.
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
version="1.0"> 
<xsl:output method="html" version="4.0" indent="yes"/>

<xsl:template match="/"> 

<html>
<body>

<center> 
   <h1>Summary Information For Experiment</h1>
   <h2> <xsl:value-of select="BustardSummary/ChipSummary/RunFolder"/> </h2> 
</center>

<h2><br/><br/>Chip Summary</h2>
<table border="1" cellpadding="5">
   <xsl:for-each select="BustardSummary/ChipSummary"> 

       <tr><td >Machine</td>
       <td > 
       <xsl:value-of select="Machine"/> </td></tr>

       <tr><td >Run Folder</td>
       <td > 
       <xsl:value-of select="RunFolder"/> </td></tr>

       <tr><td >Chip ID</td>
       <td > 
       <xsl:value-of select="ChipID"/> </td></tr>
   </xsl:for-each> 
</table> 

<h2><br/>Chip Results Summary</h2>
<table border="1" cellpadding="5">
   <tr>
   <th>Clusters</th>
   <th>Clusters (PF)</th>
   <th>Yield (kbases)</th>
   </tr>

   <xsl:for-each select="BustardSummary/ChipResultsSummary">
      <tr><td>
      <xsl:value-of select="clusterCountRaw"/> </td>

      <td>
      <xsl:value-of select="clusterCountPF"/> </td>

      <td>
      <xsl:value-of select="round(yield div 1000)"/>
      </td></tr>
   </xsl:for-each>
</table>

<xsl:if test="string(BustardSummary/Samples)">
  <h2><br/>Samples summary</h2>
  <table border="1" cellpadding="5">
    <tr>
      <th>Lane</th>
      <th>Barcode</th>
      <th>Sample</th>
      <th>Species</th>
    </tr>
    <xsl:for-each select="BustardSummary/Samples/Lane">
      <tr>
        <td><xsl:value-of select="laneNumber"/> </td>
        <td><xsl:value-of select="barcode"/> </td>
        <td><xsl:value-of select="sampleId"/> </td>
        <td><xsl:value-of select="species"/></td>
      </tr>
    </xsl:for-each>
  </table>
</xsl:if>

<xsl:for-each select="BustardSummary/LaneResultsSummary/Read">

   <xsl:variable name="numReads" select="count(../Read)"/>

   <h2><br/>Lane Results Summary
   <xsl:if test="count(../Read)>1">
      : Read <xsl:value-of select="readNumber"/>
   </xsl:if>
   </h2>

   <table border="1"  cellpadding="5">
      <tr><th colspan="2">Lane Info</th>
      <th colspan="8">Tile Mean +/- SD for Lane</th></tr>
      <tr><th>Lane</th>
      <th>Lane Yield (kbases)</th>

      <th>Clusters (raw)</th>
      <th>Clusters (PF)</th>
      <th>First Cycle Int (PF)</th>
      <th>% intensity after 20 cycles (PF)</th>
      <th>% PF Clusters</th></tr>

      <xsl:variable name="clusterCountRawMean" select="sum(Lane/clusterCountRaw/mean)"/>
      <xsl:variable name="clusterCountPFMean"  select="sum(Lane/clusterCountPF/mean)"/>
      <xsl:variable name="oneSigMean"          select="sum(Lane/oneSig/mean)"/>
      <xsl:variable name="signal20AsPctOf1Mean"   select="sum(Lane/signal20AsPctOf1/mean)"/>
      <xsl:variable name="percentClustersPFMean"      select="sum(Lane/percentClustersPF/mean)"/>
      <xsl:variable name="numLanes"            select="count(Lane/laneYield)"/>

      <xsl:for-each select="Lane">

         <xsl:if test="string(laneYield)">

         <tr><td>
         <xsl:value-of select="laneNumber"/> </td>

         <td>
         <xsl:value-of select="laneYield"/> </td>

         <td>
         <xsl:value-of select="clusterCountRaw/mean"/> +/- 

         <xsl:value-of select="clusterCountRaw/stdev"/> </td>
         <td>

         <xsl:value-of select="clusterCountPF/mean"/> +/- 
         <xsl:value-of select="clusterCountPF/stdev"/> </td>

         <td>
         <xsl:value-of select="oneSig/mean"/> +/- 
         <xsl:value-of select="oneSig/stdev"/> </td>

         <td>
         <xsl:value-of select="signal20AsPctOf1/mean"/> +/- 
         <xsl:value-of select="signal20AsPctOf1/stdev"/> </td>
        
         <td>
         <xsl:value-of select="percentClustersPF/mean"/> +/- 
         <xsl:value-of select="percentClustersPF/stdev"/> </td>
         </tr>
 
         </xsl:if>

      </xsl:for-each>

      <tr><td  colspan="13">Tile mean across chip</td></tr>

      <tr><td  colspan="2">Average</td>

      <td>
      <xsl:value-of select="round($clusterCountRawMean div $numLanes)"/> </td>

      <td>
      <xsl:value-of select="round($clusterCountPFMean div $numLanes)"/> </td>

      <td>
      <xsl:value-of select="round($oneSigMean div $numLanes)"/> </td>

      <td>
      <xsl:value-of select="round($signal20AsPctOf1Mean div $numLanes * 100) div 100"/> </td>

      <td>
      <xsl:value-of select="round($percentClustersPFMean div $numLanes * 100) div 100"/> </td>

      </tr>
   </table>
</xsl:for-each>



<xsl:for-each select="BustardSummary/ExpandedLaneSummary/Read">

   <xsl:variable name="numReads" select="count(../Read)"/>

   <h2><br/>Expanded Lane Summary
   <xsl:if test="count(../Read)>1">
      : Read <xsl:value-of select="readNumber"/>
   </xsl:if>
   </h2>

   <table border="1" cellpadding="5">

   <tr><th colspan="2">Lane Info</th>
   <th colspan="2">Phasing Info</th>
   <th colspan="2">Raw Data (tile mean)</th>
   <th colspan="9">Filtered Data (tile mean)</th>
   </tr>
   <tr>
   <th>Lane</th>
   <th>Clusters (tile mean) (raw)</th>
   <th>% Phasing</th>
   <th>% Prephasing</th>
   <th>% Retained</th>
   <th>Cycle 2-4 Av Int (PF)</th>
   <th>Cycle 2-10 Av % Loss (PF)</th>
   <th>Cycle 10-20 Av % Loss (PF)</th></tr>

   <xsl:for-each select="Lane">

      <xsl:if test="string(phasingApplied)">

      <tr><td>
      <xsl:value-of select="laneNumber"/> </td>

      <td>
      <xsl:value-of select="clusterCountRaw/mean"/> </td>

      <td>
      <xsl:value-of select="phasingApplied"/> </td>

      <td>
      <xsl:value-of select="prephasingApplied"/> </td>

      <td>
      <xsl:value-of select="percentClustersPF/mean"/> </td>

      <td>
      <xsl:value-of select="signalAverage2to4/mean"/> +/- 
      <xsl:value-of select="signalAverage2to4/stdev"/> </td>

      <td>
      <xsl:value-of select="signalLoss2to10/mean"/> +/- 
      <xsl:value-of select="signalLoss2to10/stdev"/> </td>

      <td>
      <xsl:value-of select="signalLoss10to20/mean"/> +/-
      <xsl:value-of select="signalLoss10to20/stdev"/> </td>
      </tr>

      </xsl:if>

   </xsl:for-each>
   </table>
</xsl:for-each>



<xsl:for-each select="BustardSummary/TileResultsByLane/Lane">

   <xsl:element name="a">
   <xsl:attribute name="name">Lane<xsl:value-of select="laneNumber"/>
   </xsl:attribute>
   </xsl:element>

   <xsl:variable name="numReads" select="count(Read)"/>

   <xsl:for-each select="Read">

   <br/><h2>Lane <xsl:value-of select="../laneNumber"/>
   <xsl:if test="count(../Read)>1">
     : Read <xsl:value-of select="readNumber"/>
   </xsl:if>
   </h2>

   <table border="1" cellpadding="5">

   <tr><th colspan="1">Lane</th>
   <th colspan="1">Tile</th>
   <th colspan="1">Clusters (raw)</th>
   <th colspan="1">Av 1st Cycle Int (PF)</th>
   <th colspan="1">Av % intensity after 20 cycles (PF)</th>
   <th colspan="1">% PF Clusters</th></tr>

   <xsl:for-each select="Tile">
      <tr><td>
      <xsl:value-of select="../../laneNumber"/> </td>
      <td>
      <xsl:value-of select="tileNumber"/> </td>
      <td>
      <xsl:value-of select="clusterCountRaw"/> </td>
      <td>
      <xsl:value-of select="oneSig"/> </td>
      <td>
      <xsl:value-of select="signal20AsPctOf1"/> </td>
      <td>
      <xsl:value-of select="percentClustersPF"/> </td>
      </tr>
   </xsl:for-each>
   </table>
 </xsl:for-each>

   <xsl:if test="string(Coverage)">
      <h4>Coverage plot:</h4>
      <xsl:element name="a">
      <xsl:attribute 
         name="href"> <xsl:value-of select="Coverage"/> 
      </xsl:attribute>
         <xsl:value-of select="Coverage"/>
      </xsl:element>
   </xsl:if>

   <xsl:if test="Monotemplate[.!='']">
      <h3>Monotemplate Summary</h3>

      <table border="1" cellpadding="5">
      <tr><th colspan="1">Template</th>
      <th colspan="1">Count</th>
      <th colspan="1">Percent</th>
      <th colspan="1">True 1st Cycle Intensity</th>
      <th colspan="1">Av Error Rate</th>
      <th colspan="1">% Perfect</th></tr>

      <xsl:for-each select="Monotemplate/TemplateList">
         <tr><td>
         <xsl:value-of select="Template"/> </td>

         <td>
         <xsl:value-of select="Count"/> </td>
   
         <td>
         <xsl:value-of select="Percent"/> </td>

         <td>
         <xsl:value-of select="TrueFirstCycleIntensity"/> </td>

         <td>
         <xsl:value-of select="AvErrorRate"/> </td>

         <td>
         <xsl:value-of select="PercentsPerfect"/> </td></tr>
      </xsl:for-each>
      </table>
   </xsl:if>

</xsl:for-each>
   <br/><br/><li><h3>IVC Plots</h3></li>
   <xsl:element name="a">
   <xsl:attribute name="href">IVC.htm</xsl:attribute> <p> click here </p>
   </xsl:element>


   <h3><li>All Intensity Plots</li></h3>
   <xsl:element name="a">
   <xsl:attribute name="href">All.htm</xsl:attribute> <p> click here </p>
   </xsl:element>

<hr/>
<p><font size="-2">bcl2fastq-1.8.4</font></p>
</body>
</html>

</xsl:template>


</xsl:stylesheet>
