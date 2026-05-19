---
title: "What Is GA4? Everything SaaS Teams Need to Know"
description: "GA4 (Google Analytics 4) is Google’s current analytics platform, built around event-based tracking instead of session-based data. It replaced Universal Analytics in July 2023. Unlike its predecessor, GA4 tracks user behaviour across devices and platforms in a single property. TL;DR GA4 replaced Universal Analytics in July 2023 and is now the only version of Google […]"
metaTitle: "What Is GA4? The SaaS Marketer's Guide"
metaDescription: "GA4 is Google's current analytics platform, replacing Universal Analytics. Learn how it works, what's different, and how to get real value from it."
date: 2026-04-27
slug: "what-is-ga4"
categorySlug: "analytics-attribution"
writtenBy: "vishnu-prasad"
wp_id: 3538
glossaryCategory: "Analytics & Attribution"
wp_link: "/glossary/what-is-ga4/"
toc: true
readingTime: "10 min read"
---

GA4 (Google Analytics 4) is Google’s current analytics platform, built around event-based tracking instead of session-based data. It replaced Universal Analytics in July 2023. Unlike its predecessor, GA4 tracks user behaviour across devices and platforms in a single property.

## TL;DR

- GA4 replaced Universal Analytics in July 2023 and is now the only version of Google Analytics Google actively supports.
- GA4 uses an event-based data model, which means every user interaction page views, clicks, form submissions is tracked as a discrete event.
- The platform is built for cross-device tracking, so you can follow a user from a mobile visit to a desktop conversion in one continuous session view.
- GA4’s predictive metrics use machine learning to surface insights like purchase probability and churn likelihood directly inside the platform.
- Most SaaS teams underuse GA4 because they’re still trying to read it like Universal Analytics, which produces confusing and often misleading reports.

## What Is GA4?

GA4 is Google’s analytics platform the tool that tracks how users find, interact with, and convert on your website or app. It’s not an upgrade to Universal Analytics. It’s a fundamentally different system built on a different data model.

Universal Analytics counted sessions and pageviews. GA4 counts events. Every single thing a user does loading a page, clicking a button, watching a video, submitting a form gets logged as an event with attached parameters.

That shift sounds technical, but the business implication is significant. Session-based analytics forced you to think in visits. Event-based analytics lets you think in actions. For SaaS specifically, where the path from visitor to paying customer involves dozens of micro-interactions, that’s a meaningful change.

Here’s what most guides miss: the problem isn’t that GA4 is harder to use. The problem is that teams are trying to answer Universal Analytics questions with GA4 data. The two systems don’t map cleanly onto each other, and forcing that comparison produces reports that look broken.

- Event-based tracking: Every user interaction is a named event with customisable parameters, replacing the old hit-type model of pageviews, events, and transactions.
- Cross-device identity: GA4 uses a combination of User ID, Google Signals, and device ID to stitch together a user’s journey across sessions and devices.
- Exploration reports: The Explorations section replaces the old Custom Reports interface with a more flexible, drag-and-drop analysis tool.
- Predictive audiences: GA4 uses machine learning to build audiences based on predicted behaviour useful for remarketing and paid media targeting.
- Big Query integration: The free native export to Big Query is available on all properties, not just 360, which opens up raw event-level data for SQL analysis.

Consider a SaaS tool for HR teams let’s call it something like a workforce scheduling platform. In Universal Analytics, they’d see session counts and goal completions. In GA4, they can track every step of the trial signup flow as individual events, see exactly where users drop off, and build a funnel that reflects how their product actually works not how Google’s old session model approximated it.

The shift to GA4 isn’t optional. Universal Analytics stopped processing new data in July 2023. If you’re not set up properly in GA4, you’re working with incomplete or no data.

## How Is GA4 Different From Universal Analytics?

The core difference is the data model. Universal Analytics was built around sessions a defined window of time in which a user’s activity was grouped. GA4 is built around events individual actions that can be tracked, named, and parameterised however you need.

This changes almost everything downstream: how reports are structured, how conversions are defined, how audiences are built, and how you export data.

Fast Fact: GA4’s event-based model means there’s no hard limit on the types of interactions you can track every custom event is configurable, unlike the rigid hit-type structure in Universal Analytics.

- No more bounce rate (sort of): GA4 replaced bounce rate with engagement rate, which measures sessions where a user was actively engaged 10+ seconds, a conversion, or two or more page views. A “bounced” session in GA4 is simply a non-engaged one.
- Different session counting: GA4 counts a new session when a campaign source changes mid-visit, which Universal Analytics didn’t do. This can make session counts look lower than you’re used to.
- Conversion events, not goals: Goals no longer exist. Conversions are just events you mark as conversion events. You can mark multiple events as conversions and they’ll all count independently.
- Looker Studio dependency: Many of the more detailed reports that lived natively in Universal Analytics now need to be built in Looker Studio or the Explorations section.
- Data retention limits: GA4 defaults to two months of data retention for event-level data, with a maximum of fourteen months. Historical data from Universal Analytics didn’t transfer over.

The data retention issue catches a lot of teams off guard. You can’t go back and pull three years of historical data in GA4 that window is set at the property level. If you haven’t changed it from the default, you may already be losing data you’ll want later.

Also read: [best B2B marketing agencies for SaaS and tech companies](/list/best-b2b-marketing-agencies/)

## How Does GA4 Track Events?

GA4 tracks three types of events: automatically collected, enhanced measurement, and custom. Automatically collected events fire without any configuration things like session start, first visit, and page view. Enhanced measurement events require you to toggle them on in the admin settings.

Custom events are where most of the real work happens for SaaS teams.

- Automatically collected events: These fire by default session\_start, first\_visit, page\_view, and a handful of engagement signals. No setup required.
- Enhanced measurement events: These include scroll depth, outbound link clicks, site search, video engagement, and file downloads. You enable them in the data stream settings.
- Recommended events: Google has a list of pre-named events for common actions things like sign\_up, login, purchase, and generate\_lead. Using the recommended names means GA4 can surface them in standard reports automatically.
- Custom events: Anything not covered by the above. You define the name and parameters yourself, either through Google Tag Manager or the gtag.js SDK.

Here’s what the basic custom event implementation looks like in Google Tag Manager or directly via gtag:

“`javascript

// Tracking a trial signup button click via gtag.js

gtag(‘event’, ‘trial\_signup\_click’, {

‘event\_category’: ‘engagement’,

‘event\_label’: ‘homepage\_hero\_cta’,

‘user\_type’: ‘new\_visitor’

});

“`

And in GA4 via the Measurement Protocol for server-side events:

“`bash

POST https://www.google-analytics.com/mp/collect?measurement\_id=G-XXXXXXXX&api\_secret=YOUR\_SECRET

{

“client\_id”: “123456.7654321”,

“events”: [{

“name”: “trial\_signup”,

“params”: {

“plan\_type”: “free\_trial”,

“source\_page”: “pricing”

}

}]

}

“`

The naming convention matters more than most teams realise. GA4 is case-sensitive trial\_signup and Trial\_Signup are two different events. If you’re pulling in events from multiple sources or team members, inconsistent naming will fragment your data fast.

Custom events don’t appear in standard reports automatically. You have to register them as custom dimensions or mark them as conversions before they show up anywhere useful.

## What Are GA4’s Key Reports and Where Do You Find Them?

GA4’s reporting interface is split across several areas, and the layout is genuinely different from what Universal Analytics users expect. The main navigation has four sections: Reports, Explore, Advertising, and Configure.

Reports is where you find the standard overview dashboards. Explore is where you build custom analyses. Advertising is for attribution and campaign performance. Configure is where you manage events, conversions, audiences, and custom dimensions.

Fast Fact: Most teams spend the majority of their time in the standard Reports section, but the Explorations section is where GA4 actually becomes useful for complex SaaS funnel analysis.

- Life Cycle reports: These cover acquisition, engagement, monetisation, and retention structured around the user journey rather than just traffic sources.
- User reports: These focus on demographics, technology, and user attributes rather than session-level data.
- Funnel exploration: Available in the Explore section, this lets you build multi-step funnels with open or closed steps, segment by user or session, and visualise drop-off at each stage.
- Path exploration: Shows you the actual paths users take through your site useful for finding unexpected routes to conversion or common exit points.
- Segment overlap: Lets you compare up to three user segments visually to find behavioural patterns across audience groups.

The reporting in GA4 is more powerful than Universal Analytics in most respects, but it requires more setup to get there. Out of the box, the standard reports are fairly surface-level. The real value is in Explorations, which takes some time to learn but is worth the investment.

Also read: [top B2B PPC agencies that use GA4 data to optimise paid campaigns](/list/top-b2b-ppc-agencies/)

## What Are the Biggest Mistakes SaaS Teams Make With GA4?

The most common mistake is treating GA4 as a direct replacement for Universal Analytics and expecting the same numbers to come out. They won’t. The metrics are calculated differently, the sessions are counted differently, and the attribution models don’t align.

That mismatch leads teams to conclude GA4 is “broken” when it’s actually working correctly they’re just asking it the wrong questions.

- Not adjusting data retention: The default is two months. If you don’t change it to fourteen months in Admin → Data Settings → Data Retention, you’ll lose event-level data you can’t recover.
- Marking too many events as conversions: GA4 lets you mark any event as a conversion, which is flexible but if you mark twenty events as conversions, your conversion reports become unreadable. Be selective.
- Ignoring custom dimensions: Custom event parameters don’t appear in reports until you register them as custom dimensions. Most teams fire custom events and then wonder why the data isn’t showing up anywhere.
- Not filtering internal traffic: If you don’t create an internal traffic filter and exclude your own IP ranges, your team’s activity will inflate engagement metrics especially important in early-stage SaaS where team activity is a large proportion of total visits.
- Skipping the Big Query export: The free Big Query connection is one of GA4’s most underrated features. Raw event-level data with no sampling, queryable with SQL. Most teams never set it up.

GA4’s predictive audiences are worth calling out specifically. They work best when you have enough conversion data to train the models typically a few hundred conversions per month. Below that threshold, the predictions aren’t reliable enough to act on.

This works well for mid-market SaaS products with significant traffic volume. For early-stage tools still in the hundreds of monthly visitors, the predictive features are mostly noise until you scale up the data volume.

## The Bottom Line

GA4 is the foundation of any serious SaaS analytics setup right now. The teams getting the most out of it aren’t the ones who’ve memorised every report they’re the ones who’ve invested in clean event tracking, sensible conversion definitions, and a Big Query connection that lets them query raw data without sampling. Get those three things right and GA4 becomes genuinely useful. Leave them misconfigured and you’ll spend more time doubting your data than acting on it.

If you want help making sure your analytics are feeding your paid and organic channels properly, [get in touch via our contact page](https://www.piperocket.co/contact) or explore how our [SaaS PPC service](https://www.piperocket.co/saas-ppc) uses GA4 data to improve campaign performance at every stage of the funnel.
