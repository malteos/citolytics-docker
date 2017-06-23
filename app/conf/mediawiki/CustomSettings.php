<?php

// append to LocalSettings.php

// Logo
$wgLogo = "/logo.png";
$wgEnableUploads = true;

// EventLogging
require_once "$IP/extensions/EventLogging/EventLogging.php";
$wgEventLoggingBaseUri = 'http://localhost:8080/event.gif';
$wgEventLoggingFile = '/var/log/mediawiki/events.log';
$wgEventLoggingSchemaApiUri = 'https://meta.wikimedia.org/w/api.php';

// PageImages
wfLoadExtension( 'PageImages' );

// CirrusSearch, Elastica & Citolytics
require_once( "$IP/extensions/Elastica/Elastica.php" );
require_once( "$IP/extensions/CirrusSearch/CirrusSearch.php" );

$wgDisableSearchUpdate = true;
$wgCirrusSearchServers = array( 'es' );
$wgSearchType = 'CirrusSearch';

# Enable Citolytics
$wgCirrusSearchEnableCitolytics = true;
$wgCirrusSearchDevelOptions['ignore_missing_rev'] = True;


// MobileApp
require_once "$IP/extensions/MobileApp/MobileApp.php";

// Wikibase
$wgEnableWikibaseRepo = true;
$wgEnableWikibaseClient = true;
require_once "$IP/extensions/Wikibase/repo/Wikibase.php";
require_once "$IP/extensions/Wikibase/repo/ExampleSettings.php";
require_once "$IP/extensions/Wikibase/client/WikibaseClient.php";
require_once "$IP/extensions/Wikibase/client/ExampleSettings.php";


wfLoadExtension( 'MobileFrontend' );
$wgMFAutodetectMobileView = true;

// Debug
#error_reporting( -1 );
#ini_set( 'display_errors', 1 );
$wgDebugToolbar = true;
#$wgShowDebug = true;
#$wgDevelopmentWarnings = true;
$wgShowExceptionDetails = true;
