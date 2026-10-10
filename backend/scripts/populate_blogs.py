"""One-off script to populate each domain's Blog with the content supplied by
the organizers (ADAPPT_Final content packs — one PDF per domain, each with
nine labelled sections: Domain Explainer, Discovery, Research Insight, Blog,
Real-World Application, Future/Discussion, Case Study, Technology Explainer,
Ethical/Discussion). All nine sections are concatenated into the one Blog
article per domain, verbatim from the source PDFs.

Safe to re-run: updates the existing Blog row for a domain in place rather
than creating a duplicate.

Usage:
    source venv/bin/activate
    python -m scripts.populate_blogs
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import Blog, Domain
from app.models.enums import PublishStatus

CYBERSECURITY_CONTENT = """DOMAIN EXPLAINER
Cybersecurity in Smart Homes: Where Connected Living Meets Security

Cybersecurity in smart homes is about protecting the connected devices, networks, and information that make a modern home work. This includes cameras, door locks, speakers, thermostats, lighting, appliances, and the routers, phones, and cloud services that link them together. Rather than focusing on one device, the domain looks at how the whole connected home can stay trustworthy as it grows.

Real homes are more varied than most people expect. In one large study, researchers released an open-source tool called IoT Inspector that let people observe the devices on their own networks. It collected labelled traffic from 54,094 smart home devices installed by 5,404 users [1]. Cameras, plugs, TVs, and speakers from many different makers were all sharing networks, each with its own software and habits.

That variety is why security matters beyond any single product. A 2017 analysis of the Mirai botnet traced how a large collection of mostly embedded and IoT devices, reaching a peak of around 600,000 infections, was used to overwhelm online targets with traffic [2]. The study is a useful reminder that everyday connected devices can matter well beyond the home they sit in.

Several themes run through this domain. Homes contain many devices from many makers. Everyday users are not security specialists. Protections that are too strict can be as frustrating as those that are too loose, and security touches privacy, physical safety, and convenience all at once.

Smart-home cybersecurity ultimately asks an interesting question: how can a home stay connected, convenient, and trustworthy at the same time?

DISCOVERY
Can Your Smart Home Know When It Is Under Attack?

A smart home produces a constant stream of information. A thermostat reports temperatures, a camera sends video, a speaker waits for voice commands, and the router sees which devices are talking to which online services. Most of this activity is routine.

Even routine activity carries information. Princeton researchers found that, even when a device's traffic was encrypted, the rate at which it sent data could let an outside observer infer what was happening in the home [3]. The idea works both ways: if patterns in traffic reveal what a device is doing, they may also help reveal when a device is doing something unusual.

That is the thinking behind threat detection. A system learns what normal looks like for each device and watches for departures from it. A smart plug that suddenly sends large amounts of data to an unfamiliar service at 3 a.m. might deserve a closer look.

The difficulty is that homes do not stay still. Guests visit, people travel, devices receive updates, and new gadgets arrive. Unusual activity is not always harmful, and harmful activity does not always look unusual.

This is why the problem is interesting. A system that raises too many alerts may be ignored, while one that raises too few may miss something important. Can a smart home know when it is under attack? It potentially can notice some signs, but doing so reliably in a home where "normal" keeps shifting is still an open research question.

RESEARCH INSIGHT
Teaching Smart Homes to Detect Cyber Threats

Researchers have explored learning what normal looks like rather than relying only on fixed rules. One example, N-BaIoT, takes snapshots of a device's network behaviour and trains a model called an autoencoder, a type of neural network that learns to reproduce normal patterns. Traffic the model struggles to reproduce can be flagged as anomalous. In lab experiments, nine commercial IoT devices were infected with two well-known botnets, Mirai and BASHLITE, and the authors reported that the method could detect the attacks as they were launched [4].

Another system, Kitsune, uses a group of small autoencoders that learn from the local network's traffic without needing labelled examples. Its authors reported detection performance comparable to offline methods, even when running on a Raspberry Pi, which suggests detection may not always require powerful hardware [5].

Important challenges remain. The N-BaIoT experiments used a limited set of devices in a lab, while real homes can contain far more variety, as the tens of thousands of devices seen in IoT Inspector suggest [1]. A pattern that is normal for a camera may look odd for a light bulb. Household routines change. A system that frequently mistakes harmless activity for danger may lose the user's trust, and threats evolve, so a model built on past patterns may not capture what comes next.

The broader research question is how to build detection that is accurate enough to be useful, simple enough for ordinary households, and adaptable enough to keep pace with change.

BLOG
Why Securing a Smart Home Is Harder Than It Sounds

Securing a smart home can sound like a simple checklist: use strong passwords and keep everything updated. In practice, the home is a mixed collection of products that were never designed to work as one system.

Devices come from different manufacturers and run different software. They receive updates on different schedules and offer different security features. The IoT Inspector study found devices spanning many categories and vendors sharing ordinary home networks [1]. One camera may update automatically, while an older appliance may rarely update at all.

Part of the challenge is that some basics were historically left to chance. The Mirai researchers argued that fairly simple techniques were enough to compromise large numbers of low-end devices [2]. Regulators have since started building basics into the rules. Since 29 April 2024, the UK has required connectable consumer products to avoid universal default passwords, provide a way to report security problems, and publish how long security updates will be provided [6]. These steps help, but they apply to new products, and many older devices are still in use.

People matter too. A household may include a technology enthusiast, a casual user, children, and visitors, each with different habits and different patience for extra steps.

This is why securing one device does not automatically secure the home. Devices share a network, connect to the same accounts, and often trust one another. Security is better understood as ongoing management than a one-time setup. The useful question is not "Is this device secure?" but "How do all my devices, accounts, and habits fit together?"

REAL-WORLD APPLICATION
Cybersecurity Across the Smart Home

Smart-home security is best viewed as a system, because the parts of a home are connected through shared networks, accounts, and services.

Start with the router, which carries traffic for almost everything else. The phone often acts as the remote control for cameras, locks, and thermostats. A hub may coordinate many devices at once, and cloud services store accounts, recordings, and settings behind the scenes.

These relationships mean a weakness in one place can matter elsewhere. Princeton researchers distinguish between an external observer, who sees traffic only after it leaves the home, and a local one, such as a malicious device on the home network, which can see more of what other devices are doing [7]. A neglected gadget can therefore affect how far the rest of the network can be trusted. A poorly protected account could expose every device linked to it, and a compromised phone could affect everything it is authorised to control.

The connection also reaches beyond the front door. In the Mirai case, devices in homes and businesses were enlisted to send traffic at targets elsewhere on the internet [2], showing how one household's weak point can become part of a much larger problem.

The same logic works in the helpful direction. Separating devices into different network groups, keeping software updated, and limiting what each device can access can potentially reduce how far a problem spreads.

The opportunity lies in thinking about decisions together: which devices connect to what, who can control them, and what each one really needs to access.

FUTURE / DISCUSSION
What Should a Smart Home Protect First?

When a smart home faces a security decision, a basic question arises: what matters most?

Privacy is one candidate, since cameras and microphones can capture sensitive moments. Physical safety is another, because locks, alarms, and heating affect people directly. Availability matters because a protection that switches off a heater in winter creates its own problems. Convenience counts too, since people tend to abandon protections that make daily life awkward.

Research shows these priorities can pull against one another. In the Princeton study, adding cover traffic to hide a home's activity patterns could protect privacy, at a cost of roughly 40 KB/s of extra bandwidth [3]. That may be small for some households and noticeable for others.

Policy shows the same balancing act. The U.S. Cyber Trust Mark is a voluntary label for wireless consumer IoT products, designed to help buyers compare, and in 2026 it was still being rolled out [8]. The UK sets baseline requirements for products on sale [6]. The EU's Cyber Resilience Act added reporting duties for actively exploited vulnerabilities from 11 September 2026, with wider requirements from December 2027 [9]. Each puts weight on a different part of the problem.

There is no single correct ranking. A family with young children, someone working from home, and an older adult living alone may each weigh these priorities differently. Smart-home cybersecurity involves deciding which outcomes matter most and how to balance them when they cannot all be maximised at once.

CASE STUDY
AI Detecting an Intruder in the Smart Home Network

This is an illustrative, hypothetical scenario created to explain a concept. It does not describe a real event or a specific product.

Imagine a household with a router, a security camera, a smart speaker, a thermostat, and an older smart plug. A network monitoring system supported by AI has spent several weeks learning how each device normally behaves, much like the per-device and per-channel approaches described in research such as N-BaIoT and Kitsune [4][5].

One evening, the smart plug begins contacting an unfamiliar online destination and sending far more data than usual. The router also records connection attempts from the plug toward devices it has never communicated with.

The system does not rely on one signal. It may consider the plug's usual behaviour, the timing, the volume of data, the unfamiliar destination, and whether the household is home or away. Together, these could suggest the activity is unusual enough to review.

Possible responses include sending an alert, limiting the plug's network access, or asking the homeowner whether anything has changed, such as a recent update.

Human judgement still matters. The homeowner may know the plug was just reset, or may decide to remove it entirely. The system supplies a detection and a suggestion; the person supplies context and makes the final call.

TECHNOLOGY EXPLAINER
How Can a Smart Home Recognize a Cyberattack?

Recognizing a possible cyberattack is similar to noticing that something in your home is out of place. The basic process can be thought of as:

Device Activity -> Network Data -> Security Model -> Detected Pattern -> Alert / Action

Device activity is what each device does: when it connects, what it asks for, and who it talks to. Network data is the record of that communication as it passes through the router, such as which devices connected and how much information moved.

A security model compares this record with what is normal. Research systems do this in different ways. N-BaIoT builds a separate model for each device [4], while Kitsune tracks patterns across each network channel [5]. Both look for anomalies, meaning activity that departs from the usual pattern. Other safeguards support the process. Authentication checks that a user or device is who it claims to be. Encryption scrambles content so outsiders cannot easily read it, although traffic patterns can still carry information [3].

A detected pattern is the model's finding, such as a device behaving unlike its past self. The final stage is an alert or action: notifying the homeowner or limiting a device's access.

None of these stages is perfect. A pattern is a signal rather than proof, and results depend on the data and the design. The goal is to turn everyday device behaviour into information that helps people respond sensibly.

ETHICAL / DISCUSSION
When Should a Smart Home Decide What Is Safe?

Suppose a security system detects suspicious activity. What should happen next? It might disconnect a device, lock a smart door, disable an appliance, or simply alert the homeowner first.

Acting too quickly carries risks. If the system is mistaken, it could cut off a device someone depends on, lock a person out, or switch off heating. Acting too slowly has costs as well. If the activity is genuinely harmful, waiting for a response might allow a problem to grow.

This highlights a distinction between prediction and action. Much of the research discussed in this series, including N-BaIoT and Kitsune, focuses on detection: how well a system can flag traffic that looks abnormal [4][5]. Deciding what should happen after a flag is a separate design question. A system that recommends, for example by saying "this device looks unusual," supports a person's decision. A system that acts on its own changes what happens in the physical home.

Different actions may call for different levels of independence. Limiting a low-risk device's network access might reasonably happen automatically, while anything affecting locks, safety equipment, or essential services may warrant human confirmation.

Good design may involve clear explanations, adjustable settings, and an easy way to review and reverse decisions. The challenge is not just whether a smart home can decide, but when it should, and how automation can support human control rather than replace it."""

FOODTECH_CONTENT = """DOMAIN EXPLAINER
AI in FoodTech: Where Food Meets Intelligence

AI in FoodTech is about using computational intelligence to improve different parts of the food ecosystem. This includes how food is produced, assessed, distributed, consumed, and managed. Rather than focusing on one stage, the domain looks at how data and AI can help address challenges involving food quality, safety, waste, personalization, and resource efficiency.

One important area is decision-making. Food businesses deal with changing demand, while food itself can change in quality because of storage conditions, handling, temperature, and time. AI can help identify patterns in data and support decisions before problems become larger.

AI can also help people make food choices by bringing together information that is often considered separately, such as individual preferences, dietary requirements, nutritional goals, and the food currently available.

The value of AI in FoodTech therefore lies not only in automation. It is about using information more effectively across a system where many factors are constantly changing. A useful AI application could help a restaurant prepare closer to actual demand, help identify a quality issue earlier, or help a person find a suitable choice from a changing menu.

FoodTech ultimately asks an interesting question: how can intelligence from data make the food ecosystem more efficient, informed, and responsive?

DISCOVERY
Can AI Predict What People Will Eat?

Every day, food businesses have to make decisions without knowing exactly how much food customers will want. Restaurants, cafeterias, and retailers may see demand change because of everyday behaviour, events, weather, seasonality, and other factors. This makes food demand an interesting problem for AI.

Demand forecasting attempts to estimate what is likely to happen before it happens. Instead of relying only on a fixed estimate or previous day's sales, an AI system can potentially examine multiple patterns at the same time. Historical demand can be considered alongside changing conditions to identify relationships that may not be obvious.

This becomes particularly important because food is not an ordinary inventory item. If too much is prepared or purchased, the surplus may become waste. If too little is available, customers may face shortages or reduced choice.

The interesting part is that even a small improvement in predicting demand can affect several decisions at once: how much food is prepared, how much is ordered, and how resources are allocated.

AI therefore turns demand prediction into more than a simple forecasting exercise. It becomes a way of making food operations more responsive to changing circumstances. The challenge is not simply predicting a number, but understanding which factors actually influence what people will consume.

RESEARCH INSIGHT
Teaching AI to Identify Food Quality

Food quality can change because of storage conditions, handling, temperature, contamination risks, and time. Detecting these changes early is difficult when large quantities of food need to be monitored consistently. This is one area where AI research can intersect with food quality and safety.

One approach is to use data and machine-learning systems to identify patterns associated with quality changes. Another is computer vision, where images can be analysed for visible characteristics that may indicate differences between food items. Instead of relying entirely on manual inspection, AI-based systems can potentially examine large quantities of information consistently.

However, food is naturally variable. Colour, shape, texture, and appearance can differ even when products are of similar quality. Conditions such as lighting can also affect visual information. This means an AI system needs to identify meaningful patterns rather than simply match an item to one fixed appearance.

The broader research challenge is therefore about making AI useful in environments where the data is complex and constantly changing.

In FoodTech, earlier identification of quality issues could have implications beyond inspection itself. It could affect whether food moves to the next stage of the supply chain, whether it needs further assessment, or whether it can still be managed before becoming unsafe or wasted.

BLOG
Why Personalizing Food Is Harder Than It Sounds

Choosing what to eat can look simple until several factors have to be considered at the same time. A person may have particular food preferences, dietary requirements, nutritional goals, or restrictions. At the same time, the options actually available to them may change frequently.

This creates an interesting opportunity for AI-based personalization. Instead of recommending food based on only one factor, a system could consider multiple pieces of information together and identify options that are more suitable for a particular person.

The challenge is that personalization is not simply about knowing what someone liked previously. A recommendation may need to account for what the person needs, what they currently want, and what is actually available. These factors can change from one meal, menu, or day to another.

For example, a person's preferred choice may not always align with their nutritional goals, while the most suitable option may not be available at that moment. A useful system therefore needs to work with changing information rather than treating preferences as fixed.

AI in FoodTech opens up the possibility of making food choices more informed and personalized. But it also raises an important design question: How should different preferences, requirements, goals, and available options be considered together when there is no single perfect choice?

REAL-WORLD APPLICATION
AI Across the Food Ecosystem

AI in FoodTech can be viewed as a system-level opportunity because food passes through many connected stages. Food is produced, assessed, distributed, consumed, and managed, and decisions made at one stage can influence what happens later.

Consider food demand. Restaurants, cafeterias, and retailers need to decide how much food to prepare or stock while demand is still uncertain. If estimates are too high, surplus can contribute to waste. If they are too low, shortages can reduce availability. AI-based analysis could help identify patterns in demand and support more informed decisions.

A similar idea applies to food quality. Changes caused by storage conditions, handling, temperature, contamination risks, or time may need to be identified before food moves further through the supply chain. Systems that analyse relevant information could potentially support earlier detection.

Personalization adds another layer. Food choices depend on individual preferences, dietary requirements, nutritional goals, and what is actually available.

These examples show why AI in FoodTech is broader than one application. The same underlying idea — using data to understand changing conditions — can be applied to different stages of the food ecosystem.

The opportunity lies in connecting these decisions so that food can be managed more intelligently, efficiently, and responsively from one stage to the next.

FUTURE / DISCUSSION
What Should AI Optimize For?

AI can make decisions faster and identify patterns across large amounts of information, but applying it to food creates a bigger question: what should the system actually optimize for?

Consider food demand. A system could focus on predicting demand as accurately as possible, but the goal behind that prediction might be reducing waste, avoiding shortages, improving availability, or using resources efficiently. These goals can sometimes point in different directions.

The same question appears in food quality. Detecting a possible quality issue earlier could help prevent unsafe or wasted food from moving further through the supply chain. But deciding what action should follow that detection involves more than simply identifying a pattern.

Personalization also involves trade-offs. A food recommendation system may consider preferences, dietary requirements, nutritional goals, and available options. But these factors do not always point to the same choice.

This is what makes AI in FoodTech interesting. The challenge is not only building systems that can analyse data. It is also deciding which outcomes matter and how different priorities should be balanced.

As AI becomes more involved in the food ecosystem, its impact may depend as much on the decisions it is designed to support as on the intelligence of the technology itself.

CASE STUDY
AI Reducing Food Waste

Food waste can occur at several points between purchasing ingredients and serving or selling a meal. Restaurants and supermarkets have to make decisions about how much food to prepare or order without knowing exactly what customers will consume. This creates a gap between available food and actual demand.

AI can potentially help by bringing different types of information together. Historical sales, current inventory, shelf life, consumption patterns, seasonal changes, and other relevant factors can be analysed to identify where surplus may occur and what demand could look like.

Imagine a supermarket with a particular food item approaching its expiry date. An AI-supported system could consider how quickly that item normally sells, how much inventory remains, and expected future demand. Based on this information, the business could decide whether to adjust its stock, offer a discount, or explore another way of managing the surplus.

The important idea is that reducing food waste does not necessarily begin when food is thrown away. It can begin much earlier, when decisions about what to order, prepare, store, sell, or redistribute are being made.

AI therefore creates an opportunity to move from reacting to food waste after it occurs to identifying situations where waste may occur before they become a problem.

TECHNOLOGY EXPLAINER
How Can a Camera Understand Food?

When we look at a piece of fruit, we can quickly notice its colour, shape, size, or visible imperfections. Computer vision allows AI systems to analyse similar visual information from images.

The basic process can be thought of as:

Camera -> Image -> AI Model -> Identified Characteristics -> Decision

A camera first captures an image of the food. An AI model then analyses patterns within that image and can be trained to identify characteristics such as colour, size, shape, ripeness, or visible defects. The information produced by the model can then support a decision — for example, whether an item requires further inspection or belongs to a particular quality category.

However, making a machine understand food visually is not as simple as teaching it what one perfect example looks like. Food naturally varies in appearance, and factors such as lighting, camera angle, background, and packaging can change what an image looks like.

This makes computer vision an interesting area of AI in FoodTech. Instead of relying entirely on manual visual inspection, systems can potentially process large quantities of visual information consistently.

The goal is not simply to make a camera "see" food. It is to turn visual information into useful information about food quality and characteristics that can support decisions.

ETHICAL / DISCUSSION
When Should AI Decide What Happens to Our Food?

AI can potentially support decisions about food quality, safety, demand, waste, and recommendations. But as these systems become more capable, an important question arises: how much responsibility should be given to AI?

Imagine an AI system identifies a possible quality issue in a large batch of food. If the system is correct, acting quickly could help prevent unsafe food from moving further through the supply chain. But what if the system is wrong? Discarding the entire batch could result in unnecessary food waste.

A similar question appears in personalization. An AI system may recommend a particular food based on someone's preferences, dietary requirements, or nutritional goals. But should the system make that decision independently, or should the person remain responsible for choosing?

This creates a distinction between AI making a prediction and AI making a decision. An AI system might identify a possible problem, estimate demand, or suggest an option. A human professional could then use that information alongside other factors before deciding what should actually happen.

The challenge is therefore not simply whether AI can make a food-related decision. It is about determining when AI should act independently, when human judgement is necessary, and how the two should work together."""

ROBOTICS_CONTENT = """DOMAIN EXPLAINER
Robotics and Automation in Natural Disaster Management

Robotics and automation in natural disaster management is about using robots, autonomous systems, drones, sensors, and intelligent machines to support people before, during, and after disasters.

This includes how disasters are detected, how affected areas are mapped, how victims are located, how supplies are delivered, and how dangerous environments are monitored. Rather than focusing on one stage, the domain looks at how robotic systems can assist humans when conditions are too dangerous, inaccessible, or unpredictable for conventional response methods.

One important area is information gathering. After an earthquake, flood, landslide, or other disaster, responders may not immediately know which areas are safe, which structures are damaged, or where people may be trapped. Robots and drones can collect information using cameras, thermal sensors, microphones, GPS, and other sensing technologies.

Robotics can also support physical tasks. Ground robots may move through damaged structures, drones may survey large areas from above, and automated systems may help transport equipment or essential supplies.

The value of robotics in disaster management therefore lies not only in replacing human effort. It is about extending what humans can do in environments where time, information, accessibility, and safety are major challenges.

Natural disaster management ultimately asks an important question: How can robots and automated systems help humans respond to disasters faster, more safely, and with better information?

DISCOVERY
Can Robots Find People Where Humans Cannot?

After a natural disaster, one of the most important tasks is locating people who may be trapped, injured, or isolated. However, damaged buildings, unstable structures, flooding, debris, smoke, and limited visibility can make search operations extremely difficult.

Search and rescue attempts to identify where people may be located and determine how responders can reach them. Instead of relying only on human search teams, robotic systems can potentially enter environments that are difficult or dangerous for people.

Drones can provide an aerial view of affected areas and identify damaged buildings, blocked roads, flooded regions, or groups of people. Ground robots can move through rubble or confined spaces while transmitting images and other sensor information to operators.

Some systems can also use thermal cameras, microphones, or other sensors to identify signs that may indicate human presence. This allows responders to gather information without immediately sending people into the most dangerous areas.

The interesting part is that finding a person is only the beginning. A robot may identify a possible survivor, but responders still need to determine how to reach them, whether the structure is safe, and what kind of assistance is required.

Robotics therefore turns search and rescue into more than a problem of movement. It becomes a problem of sensing, interpreting information, navigating uncertainty, and deciding what should happen next.

The challenge is not simply building a robot that can enter dangerous environments, but making sure the information it provides is useful enough to support real rescue decisions.

RESEARCH INSIGHT
Teaching Robots to Understand a Disaster Environment

Natural disaster environments are very different from the controlled environments in which many robots are normally tested. Roads may be blocked, buildings may collapse, visibility may be poor, and familiar landmarks may no longer exist.

This creates an interesting research challenge for robotics. A robot needs to understand its surroundings while dealing with incomplete, changing, and sometimes unreliable information.

One approach is to combine multiple sensors. Cameras can provide visual information, while LiDAR, thermal sensors, microphones, GPS, inertial sensors, or other systems can provide additional information about the environment.

Another area of research is autonomous navigation. A robot may need to identify obstacles, estimate its position, create a map, and determine a route without relying entirely on predefined paths.

For example, a robot entering a damaged building cannot assume that a doorway, staircase, or corridor is still usable. The environment may have changed since the original building was constructed.

This makes disaster robotics different from ordinary automation. The system must operate when the environment itself is uncertain.

The broader research challenge is therefore about creating robots that can perceive, adapt, and operate safely when the conditions they encounter cannot be completely predicted in advance.

Better sensing and navigation could allow robotic systems to provide responders with more reliable information while reducing the need to expose people to unnecessary risks.

BLOG
Why Using Robots During Disasters Is Harder Than It Sounds

At first, using robots during a natural disaster may seem straightforward. Send a drone into the affected area, locate people, map the damage, and allow rescue teams to respond.

Real environments are rarely that simple.

A disaster can change an environment within minutes. Roads can become inaccessible, buildings can collapse further, communication networks can fail, and weather conditions can change. A robot designed to operate in a normal environment may suddenly encounter conditions it was never trained or tested for.

There is also a difference between collecting information and understanding it.

A drone may capture thousands of images of a damaged region, but responders still need to determine which information matters. A ground robot may detect an object beneath rubble, but that detection may need to be verified before a rescue operation begins.

Communication is another challenge. A robot may be technically capable of operating in a disaster zone but become less useful if it loses its connection to the human operator.

This is why disaster robotics is not simply about making machines more autonomous. It involves designing systems that can work with humans, communicate useful information, handle uncertainty, and continue functioning when parts of the surrounding infrastructure are unavailable.

A successful disaster-response robot therefore needs more than movement.

It needs to know what it can detect, what it cannot determine, when it should continue operating, and when a human should take over.

That makes the problem as much about system design and decision-making as it is about robotics.

REAL-WORLD APPLICATION
Robotics Across the Disaster Management Cycle

Robotics and automation can be viewed as a system-level opportunity because natural disaster management involves several connected stages.

Before a disaster, automated systems can help with monitoring and early detection. Sensors and drones can collect information about environmental conditions, infrastructure, water levels, or other indicators that may help authorities understand developing risks.

During a disaster, robots can support emergency response. Drones can provide aerial images, ground robots can investigate hazardous areas, and automated systems can help identify damaged infrastructure or possible locations of survivors.

After the immediate emergency, robotic systems can support damage assessment and recovery. Drones can map affected regions, robots can inspect damaged structures, and automated systems can help monitor areas that remain unsafe for people.

Consider an earthquake. Immediately after the event, responders may need information about collapsed structures, blocked roads, and areas where people could be trapped. Aerial drones could provide a wider view while ground robots could investigate specific locations.

A similar idea applies to floods. Automated aerial systems can survey flooded areas, while robotic or remotely operated systems may help inspect locations that are difficult or dangerous for rescue teams to reach.

These examples show why robotics in disaster management is broader than one particular robot or application.

The same underlying idea — using machines to gather information, access difficult environments, and support human decisions — can be applied across different stages of disaster management.

The opportunity lies in connecting these systems so that information collected during one stage can help responders make better decisions during the next.

FUTURE / DISCUSSION
How Much Should a Disaster-Response Robot Decide on Its Own?

Robots can move, sense their surroundings, analyse information, and in some situations make decisions without continuous human control. But disaster environments raise a larger question: How much independence should a robot have when human lives may be involved?

Consider a rescue robot searching a damaged building. An autonomous system could identify a possible route and decide to move toward it. However, the route may pass through an unstable section of the building.

If the robot is too dependent on a human operator, valuable time may be lost. If it is given too much independence, it may make a decision that a human responder would not have made with the same information.

The same problem appears with drones. An autonomous drone could identify a possible survivor and determine a flight path, but changing weather, restricted airspace, or other aircraft could create additional risks.

This creates a balance between automation and human oversight.

A system could handle routine tasks independently while requesting human approval for decisions with greater consequences. For example, a robot could autonomously map an area but require a human operator before entering a potentially unstable structure.

The future challenge is therefore not simply making robots more autonomous.

It is deciding which decisions should be automated, which should require human approval, and how humans and machines should work together when time and information are limited.

As robotic systems become more capable, their usefulness may depend as much on how responsibility is divided between humans and machines as on the technology itself.

CASE STUDY
Robots Supporting Search and Rescue After an Earthquake

Earthquakes create environments where traditional search and rescue can become extremely difficult. Buildings may collapse, roads can become blocked, and unstable structures may make it dangerous for rescue teams to enter immediately.

Imagine a response team arriving at an earthquake-affected area where several buildings have partially collapsed.

The first challenge is understanding the situation. Drones could be used to survey the affected region and create updated visual maps. This could help responders identify damaged buildings, blocked roads, and areas requiring immediate attention.

Ground robots could then be used to investigate selected locations. A robot equipped with cameras and other sensors could move through areas where sending a person immediately would be risky.

The robot could transmit information back to a human operator. If it detects something that may indicate a survivor, the rescue team could use that information to determine how to proceed.

The important point is that the robot does not necessarily replace the rescue team.

Instead, it can become an additional layer between responders and hazardous environments.

The process can be viewed as:

Disaster -> Robotic Survey -> Information Collection -> Human Assessment -> Rescue Action

This approach could allow responders to understand dangerous environments before entering them.

However, the effectiveness of the system would depend on several factors, including battery life, communication, mobility, sensor performance, environmental conditions, and the ability of operators to interpret the information being received.

The broader lesson is that disaster robotics is not about sending a machine into a dangerous area simply because it can go there.

It is about using that machine to provide useful information that can improve how humans respond.

TECHNOLOGY EXPLAINER
How Does a Robot Navigate Through a Disaster Zone?

When humans move through an environment, we naturally use our vision, hearing, memory, and understanding of the surroundings to decide where to go.

A robot needs technological systems to perform similar tasks.

A simplified disaster-navigation process can be thought of as:

Sensors -> Environment Data -> Mapping / Perception -> Path Planning -> Movement -> New Sensor Data

Sensors first collect information about the environment. A camera can provide images, while LiDAR or other distance sensors can help determine the position of objects and obstacles.

The robot can then process this information to understand its surroundings. Depending on the system, it may create a map of the area or identify important features such as walls, debris, people, or pathways.

Path-planning algorithms can then help determine where the robot should move.

However, disaster environments make this process more complicated.

A path that appears safe may become blocked. A structure may shift. Dust or smoke may reduce visibility. GPS signals may be unavailable indoors or around damaged infrastructure.

This means a disaster robot cannot always depend on a fixed map.

It may need to continuously update its understanding of the environment as new sensor information becomes available.

The goal is therefore not simply to make a robot move from one location to another.

It is to allow the robot to continuously sense, understand, plan, and adapt to an environment that may change while it is operating.

ETHICAL / DISCUSSION
When Should a Robot Take Control During a Disaster?

Robotic systems can potentially support decisions involving search, rescue, monitoring, transportation, and damage assessment. But as these systems become more capable, an important question arises: Who should be responsible when a robot makes a critical decision?

Imagine an autonomous rescue robot identifies two possible routes to a trapped person. One route is shorter but passes through an unstable section of a building. The other is safer but takes considerably longer.

An automated system could estimate the risks and select a route. But should it be allowed to make that decision independently when the consequences could affect a person's safety?

A similar question appears with autonomous drones. A drone may identify a possible survivor, but deciding how to respond could require information that cannot be determined from the drone's sensors alone.

There is also the possibility of incorrect information. A robot may misidentify an object, lose communication, experience a sensor failure, or misunderstand a damaged environment.

This creates an important distinction between a robot providing information and a robot making a decision.

A robotic system might detect a possible survivor, identify a dangerous structure, or suggest a route. A human responder could then consider that information alongside other factors before deciding what should actually happen.

This creates the idea of human-in-the-loop disaster response.

For example:

Robot detects -> Robot reports -> Human evaluates -> Human approves -> System acts

For routine and low-risk tasks, greater automation may be practical. For decisions involving significant safety consequences, human involvement may remain important.

The challenge is therefore not simply asking whether robots should be used in disasters.

It is about determining when robots should act independently, when humans should remain involved, and how responsibility should be shared between automated systems and the people operating them."""

BLOGS = [
    {
        "slug": "cybersecurity-smart-homes",
        "title": "Cybersecurity in Smart Homes: Where Connected Living Meets Security",
        "content": CYBERSECURITY_CONTENT,
    },
    {
        "slug": "ai-foodtech",
        "title": "AI in FoodTech: Where Food Meets Intelligence",
        "content": FOODTECH_CONTENT,
    },
    {
        "slug": "robotics-disaster-management",
        "title": "Robotics and Automation in Natural Disaster Management",
        "content": ROBOTICS_CONTENT,
    },
]


def run() -> None:
    db = SessionLocal()
    try:
        for entry in BLOGS:
            domain = db.query(Domain).filter_by(slug=entry["slug"]).one_or_none()
            if domain is None:
                print(f"Domain not found: {entry['slug']} — skipping")
                continue

            blog = db.query(Blog).filter_by(domain_id=domain.id).one_or_none()
            if blog is None:
                blog = Blog(domain_id=domain.id)
                db.add(blog)
                print(f"Creating blog for {domain.name}")
            else:
                print(f"Updating existing blog for {domain.name}")

            blog.title = entry["title"]
            blog.content = entry["content"]
            blog.status = PublishStatus.PUBLISHED

        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
