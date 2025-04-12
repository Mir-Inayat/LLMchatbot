(= (getThreatEntities) (match &self (Inheritance $name ThreatEntity) $name))
(= (getDefenseTechnologies) (match &self (Inheritance $name DefenseTechnology) $name))
(= (getAttackVectors) (match &self (Inheritance $name AttackVector) $name))
(= (getDataTheftThreats) (match &self (Inheritance $name DataTheft) $name))
(= (getNetworkSecurityTools) (match &self (Inheritance $name NetworkSecurity) $name))
(= (getEndpointSecurityTools) (match &self (Inheritance $name EndpointSecurity) $name))
(= (getSecurityMonitoringTools) (match &self (Inheritance $name SecurityMonitoring) $name))


(= (getThreatMitigations $threat)
   (match &self (MitigatedBy $threat $defense) $defense))

(= (getAllMitigations)
   (match &self (MitigatedBy $threat $defense) 
          (, $threat $defense)))

(= (getDefensesForAttackVector)
   (match &self 
    (, (Inheritance $attack AttackVector)
       (MitigatedBy $attack $defense)) 
    (, $attack $defense)))

(= (getThreatDetectionTools)
   (match &self (DetectedBy $threat $tool) 
          (, $threat $tool)))

(= (getToolsBySecurityDomain $domain)
   (match &self (Inheritance $tool $domain) $tool))

(= (findMitigationsByDefenseTool $tool)
   (match &self (MitigatedBy $threat $tool) $threat))

   