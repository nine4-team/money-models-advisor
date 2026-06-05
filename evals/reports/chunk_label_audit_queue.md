# Chunk Label Audit Queue

Rows below include the information needed to adjudicate the label: query, chunk text, both model labels, both model notes, and retriever ranks.

## 1. `paraphrase_buy_more_units::rollover-upsell:4`

**Query:** Customers already want the thing. I want them to commit to more sessions up front without making it feel like a discount. What structure fits?

**Query type:** `paraphrase`

**Chunk:** `rollover-upsell:4` from `rollover-upsell`

**Retriever ranks:** dense-openai rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Describes rollover upsells that can encourage customers to commit to longer agreements, fitting the query's need for structure. |
| Subagent first pass | gpt-5.5 | 0 | Rollover credit is for applying a prior purchase toward another offer, not getting customers to buy more sessions up front. |

**Chunk text:**

```text
would, but I've got three months left in this service agreement." You say, "No worries.Whatever you have, the three months, I'll credit it towards mine and I'll just make mine a two-year agreement. So you'd say like, "Hey, John, saw your negative review on, uh, their product and it really upset me. To make it up to you, I'll credit whatever payments you have left with them to switch to ours. This way you don't lose a thing and you start getting the benefits now. Fair enough?" 'Cause that way you don't have to wait for that thing to expire and pay and then wait to get the benefits. You can start getting the benefits now, and you don't lose anything, and I get the customer. Membership. So this is where you spread the first purchase over time. So who? Current customers. What? 12-month membership. How? Spread over the first purchase. So if somebody comes in, buys a block of service, uh, or, or of membership time, as- soon as they do, you can then offer to apply the entire amount towards more time, like 12 months. I can do rollover upsells anytime, I just prefer to do, to do them, right then. All right, so this is the important points. Uh, use rollover, uh, offers to attract new customers. For example, you roll over some or all of the customers paid. somebody else towards your thing, and you can find leads by scraping contact information from negative product reviews wherever available. You can do rollover upsells before refunding. This has solved me tons of cus- saved me tons of customers and cash. If you did a bad job, hey, it happens, rollover for a do-over. And if they want something different, you can rollover the purchase toward that thing in- instead. Previous customer, uh, are still customers, upsell them. These are win-backs, so reach out to old customers, six plus, plus months, uh, from their last purchase. Look at how much they paid, decide how much you wanna give them, offer it. Example, I made personalized videos. This is me personally. I made personalized videos for 200 past customers. This is before AI and all that stuff. It took me like two days, um, offering them $4,000 of credit to return. Add urgency to rollover upsells, so make them one-time only. So this is a key point. So this is optional. It's up to you, but this is how I prefer to do it. Make the moment you present the offer the only time to take the offer so they don't get to sleep on it. So you wanna surprise and delight them with this credit or this discount.
```

## 2. `exact_client_financed_acquisition_levels::cac:12`

**Query:** What are the client-financed acquisition levels?

**Query type:** `exact_framework`

**Chunk:** `cac:12` from `cac`

**Retriever ranks:** dense-openai rank 4, hybrid-rrf rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | This chunk explains customer-financed acquisition and its relationship with CAC, directly relevant to the query. |
| Subagent first pass | gpt-5.5 | 0 | Discusses attraction offers and demand for CFA, but not the three client-financed acquisition levels. |

**Chunk text:**

```text
doing. Um, you splinter out the thing. Now, I talk about this at length in the $100 million offers course. I'm not gonna break it down now, but basically, lots of different components to your offer, you have lots of different features. You take one feature off. You say, "This feature is 99% off now." Great. That's where the discount is. And then you sell the rest of it. All right? And so whatever you break off, it has to be something that's well-understood or it's not gonna work. All right? That's kind of the thing I was talking about earlier. People have to have an understanding of it. Um, the cons are you got the bargain hoppers, right? People who, you know, complain about this, but really they, they're already, you know, uh, they're already customers. They're easier to upsell though than somebody who's cold. So yeah. All right. So the objective is that attraction offers are the first step in the four prongs because if you don't have interest, you don't have anything, right? And so customer-financed acquisition requires demand. And a big difference between CAC and GP, having low cost or free front ends is a strong way to do it. So lots of demand, free big front ends, drives more in. All right. So these things are going to be interchangeable throughout the remainder of these trainings. So if you see $19 chiropractor visit, it can be just as much a free chiropractor visit. The whole thing will work. But if you're like, you insist on doing this, fine, do that. If you insist on doing this, fine, do that. It does not matter. All the money models that I will show you can have free or discount interchange and they will both work. Kaboom. These are the ways that you can improve your CAC. So with that being said, CAC is covered. Now we go into gross profit.
```

## 3. `exact_client_financed_acquisition_levels::cac:0`

**Query:** What are the client-financed acquisition levels?

**Query type:** `exact_framework`

**Chunk:** `cac:0` from `cac`

**Retriever ranks:** dense-openai rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | This chunk provides a detailed explanation of CAC, which is essential for understanding client-financed acquisition levels. |
| Subagent first pass | gpt-5.5 | 0 | Defines and calculates CAC, but does not provide the client-financed acquisition levels. |

**Chunk text:**

```text
So, cost to acquire a customer, AKA CAC. Let's dive in. Cost to acquire a customer, again. So, let's start with definition. All right, cost to acquire a customer, all the costs required to sell a new customer, so, that's the advertising dollars, the payroll to a media buyer, creative team, software that you, that the team uses to make advertising and sales commissions, salaries, the managers of those teams, everything that it costs you. So, a lot of people... And if you want, you can delineate how much does it cost if you use paid ads, for example, how much it costs us in media spend versus how much is our, sometimes people call it fully loaded CAC. Uh, you can have both those numbers separated out, which I think is wise, kind of like media CAC versus fully loaded. Uh, but at' the very basics now, that only really applies to paid media. If you, acquire customers via outbound, payroll is gonna be the majority of your CAC. If you. use, uh, content to get customers as your primary acquisition, uh, method, then it's just gonna be the cost of the payroll for the team that does all the distribution of content and editing and whatnot. But most companies, especially if you're bigger, are gonna have multiple different versions of that, which is why you just look at everything and you look at how many customers you got, you divide it out and you're like, "That's our, cost per customer." So if we're trying to get unlimited customers, we better be sure we know what our ca- own costs, uh, to make sure that we can actually pay for it so that we can get unlimited new customers. All right, so let's calculate it together. So if you use outreach as your primary way of getting customers, then you use, let's say, $200 a month in email software and you pay someone $3,000 a month to do cold email prospecting for you, then emails become appointments that turn into eight sales per month. And so then you pay your salesperson $100 per sale. So then what's CAC, right? This is like a ChatGPT prompt word problem. But fundamentally, this is what it looks like for you as a business owner. So this is how we, this is how we calculate it. So the total cost for eight sales means that you have a $3,000 emailer plus a $200 software plus 800 bucks in commissions, which is eight sales times $100 equals four grand. All right? So now, we divide that by the number of new customers, which is $4,000 divided by eight new customers equals 500 bucks per
```

## 4. `diagnostic_free_offer_overload::cac:4`

**Query:** Our free workshop dropped lead cost from $80 to $12, but sales booked per 100 leads fell and support time exploded. Is the free offer actually working?

**Query type:** `diagnostic_numeric`

**Chunk:** `cac:4` from `cac`

**Retriever ranks:** dense-openai rank 2

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 0 | The chunk discusses marketing strategies but does not provide relevant evidence regarding the effectiveness of the free offer. |
| Subagent first pass | gpt-5.5 | 2 | Directly addresses free offers lowering lead cost while creating too much volume if the business is not prepared to follow up. |

**Chunk text:**

```text
was a famous marketer who used to, he used to, on the side, teach marketing classes, and he talked about believability. And so he'd always run this test once a year where he'd run an ad that says, "Give me $100 and I will give you $1,000 back. Call this number," and no one would call. And the main reason was no one believed it. It was too good to be true. Now, to be fair, people are s- dumber now, and so maybe it would work now. But when he would run these tests, we'd have to something, you know... Uh, we'd have to run something. Uh, maybe... But, like, the point hopefully remains. All right, the next is, I've seen this split test work more times than I care for, but if you advertise something that can help you make an extra $5,000 a month versus something that helps you make an extra $500 a month, this one gets more opt-ins. And so you're like, "How could a lower result get more people to want it?" And it's because more people believe it. Kind of interesting. The last reason that people don't want your free thing is 'cause it's the wrong people seeing it. So it's like if, if I'm getting a free gym membership that's offered in Ohio, I'm never in Ohio, so I don't really care. And so if you're selling, you know, fur coats to, you know, Arizonans in the summer, probably not. the right market. Even if it's like, "Hey, it's free," it's like, "I'm just never gonna wear it," right? Now, there's intrinsic value to fur coats, but you' get the idea. All right, and so big three is that, I like, testing this, because if you give stuff away for free, then you know that' if people don't want it, you change what it is or how you describe it, they don't believe you can give it to them, or you're showing to the wrong people. All of these things are great feedback for us. So here are the pros of free, is that you will get more leads for free and you will get lower cost leads when you market or advertise with free. Here are the cons of free, is that the volume can be a double-edged sword if you're not prepared for it. So if you use some of the stuff in this book, in this training, you're gonna get way more leads than ever you, ever you used to. And so what'll happen is you'll get way more people reaching out, and if you don't have the manpower or the time to reach out to all these leads,
```

## 5. `diagnostic_free_offer_overload::cac:11`

**Query:** Our free workshop dropped lead cost from $80 to $12, but sales booked per 100 leads fell and support time exploded. Is the free offer actually working?

**Query type:** `diagnostic_numeric`

**Chunk:** `cac:11` from `cac`

**Retriever ranks:** dense-openai rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Discusses the effectiveness of free offers in generating leads and sales, directly relevant to the query. |
| Subagent first pass | gpt-5.5 | 0 | Discusses discount offers and card-on-file mechanics, not the free workshop volume, booking-rate, or support-load diagnosis. |

**Chunk text:**

```text
for cheap leads, meaning you don't have to ever worry about, like, anybody saying that you did a bait and switch or anything like that. So if you charge people for stuff, then there's, there's really nothing to say about it. All right, number two is that you can actually collect some money, which is decent, right? I mean, some money is better than no money, okay? Um, people do come expecting to spend some money. So this, to be fair, this is my belief on this. I believe that the reason that the discounted people come in and buy more is because salespeople believe that. I don't believe it actually has any difference because when we talked about the free versus not free, the close rates were the same. So I think it's more that salespeople feel more convicted, but when I look at the data, it doesn't make much of a difference because I could equally say, "These people are just looking for cheap stuff." Works the same way. It just depends on what narrative you wanna tell the salesperson. Um, these work, and this is probably the most important one, these work exceptionally well as two-step sales. Here's why. If you get someone's card before they come in, then when you, when they come in, you can then make the upsell and say, "Do you wanna use the card you have on file?" And so the key is that you have the card more than what you charge them for. So it's like you almost wanna charge them for the cheapest possible thing to make sure the card works so that when they come in, you can have a seamless upsell into the really expensive thing. And so that's what creates the upsells that are smooth as butter, point five. Now, here's the cons of discounts. If you don't do it right, you're giving away... You don't ever give away the core service at a discount. You give away a break- broken off piece of the core service or something extra that you create and then create a huge discount on it, all right? And so you don't give away core offers that has, or stuff that has hard costs unless you, like, really know what you're doing. Um, you splinter out the thing. Now, I talk about this at length in the $100 million offers course. I'm not gonna break it down now, but basically, lots of different components to your offer, you have lots of different features. You take one feature off. You say, "This feature is 99% off now." Great. That's where the discount is. And then you sell the rest of it. All
```

## 6. `confusable_bonus_vs_discount::waived-fee:4`

**Query:** For retention, should I give people a cheaper monthly price, or should I give them something valuable every month that makes staying obvious?

**Query type:** `confusable`

**Chunk:** `waived-fee:4` from `waived-fee`

**Retriever ranks:** dense-openai rank 2

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Discusses how fees can incentivize customers to stay, which is crucial for retention strategies. |
| Subagent first pass | gpt-5.5 | 0 | Discusses fee-based stickiness and cancellation costs, a different mechanism than discount versus bonus retention. |

**Chunk text:**

```text
of like guardrails to keep someone on point during the rough months can help them overall see success. And I believe that. So that's not just not, that's not just wordsmithing. That's true. Um, and this vehicle or pricing structure, money model, allows you to build incentives around that. All right. So fees get them to start. People get value out of committing immediately because they avoid a fee. People want to avoid fees, so more people sign up to continuity. Mission accomplished. Hooray. That's how this works. Fees also get them to stick, which is lovely. So people will stick for the same reason they started, by sticking to avoid the fee. So people quit for millions of reasons, but by incurring an additional cost, a larger fee, in order to cancel, their original reason for quitting immediately shrinks compared to the value of avoiding the fee. In English, if the cost to quit exceeds the cost to stay, they will probably stay. Presenting the fee. Justify the fee by explaining the cost of taking on new customers for longer term programs. Basically, if they want short term flexibility, they pay their own setup costs. If they commit to staying long term, we'll pay their setup costs for them. All right? If someone asks for additional reason, just say, "It costs us money to get you started. If you only want to test this out, you cover those costs. If you commit to longer, I'll cover them." Now, if more than 5% of people want to cancel early, look into that. Pricing incentivizes sticking, but it can't and shouldn't overcome a terrible product. You want to nudge them, not handcuff people into paying for something they hate, 'cause then they'll just hate you. Now, if you want more upfront cash, have a smaller fee. A smaller fee encourages more people to go month-to-month. This is the same, uh, difference we had with the earlier version with the continuity bonus offer. Same idea, except this is just a fee rather than a program, but some people will pay, and I'll tell you what my guess would be to get 50/50 to sign up, which would be a 33% increase, uh, a smaller fee will get more people to go month-to-month. A larger fee will encourage more people to make the commitment. But if you need more cash upfront, then you can make the fee one and a half to three times the monthly rate, and that will get more people to choose that more flexible option. And when you do this, more people will take it. Great. And you get more cash upfront. So you can drop the fee after
```

## 7. `confusable_bonus_vs_discount::waived-fee:3`

**Query:** For retention, should I give people a cheaper monthly price, or should I give them something valuable every month that makes staying obvious?

**Query type:** `confusable`

**Chunk:** `waived-fee:3` from `waived-fee`

**Retriever ranks:** dense-openai rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Explains how waiving fees for longer commitments can incentivize customers to stay, directly addressing retention strategies. |
| Subagent first pass | gpt-5.5 | 0 | Waived-fee commitment mechanics are adjacent retention guardrails, not the cheaper monthly versus recurring bonus choice. |

**Chunk text:**

```text
thousand dollars a month, fee is $5,000 if they pay month to month. Option A, pay one time five grand plus a thousand dollars for the first month, then pay $1,000 a month thereafter, cancel whenever you want. Option B, waive the $5,000 if you commit to 12, pay $1,000 per month, only pay the $5,000 fee if you break your commitment early. Boom. Very simple, very straightforward. There's the visual. If you want, you can do a different version of this where you keep, uh, the month to month rate higher. So if they cancel, the discounted commitment, you bill the difference. All right? So let's say, uh, they, basically the longer they stay, the bigger the cancellation rate. So if they've accrued, you know, uh, $177 of savings or $67 of savings every single month on their commitment, the day they wanna, they wanna break the contract, they pay the difference in savings up to that point. Now let's do some important points. So four variables for this method. You've got the commitment length, you've got the commitment rate, you've got the month to month rate, and you've got the fee that they're gonna waive or not. There are more versions of this beyond the two that I shared. You can figure them out on your own. Now, I had an earlier version of this that had like nine different versions and my editor was like, "You're honestly just gonna confuse people, so don't do that." So fundamentally though, you can mix and match these however you want. You can have a, like the rate difference between the people who commit can be less. You can have, uh, the length be a variable. Uh, the rate that you charge month to month is different, the fee that you waive. So all of those things kind of go into this deal structure. The recommendation that I have is a model that works, which is take the price, multiply it by five, make that the fee, waive it-And that holds, that basically hangs over their head the whole time. And if you want, again, the ethical reason for this is that many businesses and many services have emotional ups and downs. They're volatility for customers. And so having something kind of like guardrails to keep someone on point during the rough months can help them overall see success. And I believe that. So that's not just not, that's not just wordsmithing. That's true. Um, and this vehicle or pricing structure, money model, allows you to build incentives around that. All right. So fees get them to start. People get value out of committing immediately because they avoid a fee. People
```

## 8. `confusable_bonus_vs_discount::waived-fee:2`

**Query:** For retention, should I give people a cheaper monthly price, or should I give them something valuable every month that makes staying obvious?

**Query type:** `confusable`

**Chunk:** `waived-fee:2` from `waived-fee`

**Retriever ranks:** bm25 rank 3, hybrid-rrf rank 1

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Discusses how waived fees can help retain customers by making it more costly to leave, directly relevant to retention. |
| Subagent first pass | gpt-5.5 | 0 | Waived-fee explanation is about making leaving cost more than staying, not the queried discount-or-bonus choice. |

**Chunk text:**

```text
which case it basically gets them through that initial churn point, and then after that there's no financial reason to leave the back half of the contract. So we take the greater risk if they pay month to month, but they take a greater risk if they commit. And so if a customer chooses month to month, we lower our risk with the startup fee. But we lower their risk year to year by waiving those fees. And if they commit and they wanna quit early, then okay, they pay the fee as though they had paid month to month from the beginning. Very simple. Bottom line is that customers will stay longer if leaving costs more than staying. And to make this equitable, if they stay the full term, they can cancel if they choose with no fee. That's what makes it fair to both parties. So if you need to feel better about yourself for charging these things, uh, whether real or made up, you should get that looked at. But if you need a reason why, well, here's a perfectly reasonable also made up reason for you. You can say this. "Whenever we onboard a new customer, it always takes more resources than an existing customer who's been with us for multiple months. So in order to give you the best experience, we charge a one-time onboarding fee, setup, activation, engagement, enrollment," whatever made up thing you wanna say, "to give you the experience, that experience. So you'll never have to pay it again and it's for your own benefit so you get the most out of your experience. Now, we know that if you learn how to use our services the right. way, you'll be 23.7X times more successful." So you can say initiation, onboarding, enrollment, startup, setup, processing, activation, build, commencement. You can just use whatever words you want and then put the word "fee" afterwards, and that's what it. can be. So that is our description. Let me give you some examples. So we'll use all combinations, but we'll assume $5,000 onboarding fee and a thousand dollars a month for all of them. Okay? So waived fee with commitment. This is my personal favorite. It's clean and simple. Commitment's 12 months, monthly rate's a thousand dollars a month, fee is $5,000 if they pay month to month. Option A, pay one time five grand plus a thousand dollars for the first month, then pay $1,000 a month thereafter, cancel whenever you want. Option B, waive the $5,000 if you commit to 12, pay $1,000 per month, only pay the $5,000 fee if you break your commitment early. Boom. Very simple, very straightforward. There's the
```

## 9. `confusable_bonus_vs_discount::waived-fee:1`

**Query:** For retention, should I give people a cheaper monthly price, or should I give them something valuable every month that makes staying obvious?

**Query type:** `confusable`

**Chunk:** `waived-fee:1` from `waived-fee`

**Retriever ranks:** hybrid-rrf rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Details the structure of waived fees and how they encourage long-term commitments, which is relevant for retention strategies. |
| Subagent first pass | gpt-5.5 | 0 | Explains waived setup fees and cancellation terms, not continuity discounts or monthly value bonuses. |

**Chunk text:**

```text
a one thou- you know, a thousand dollar a month continuity plan, right? You could say, "Cool, this is 5,000 down, then a thousand bucks month to month. Or I will waive the $5,000 fee and it will be free with a 12-month commitment at $1,000 a month, and you pay that if you wanna cancel early." So this is fundamentally a neat cancellation term. Fundamentally it's, what it' is, but because we pair it as a price on the front end, it becomes a very strong sales thing too. So with the other version, we use the three, months free or whatever to get someone in, and then we say, "Cool, you have to pay the difference if you cancel early." Here, we sell them on the vacation and we say, "We have this massive onboarding fee, but I'll waive it if you sign up for a commitment." Then that' also hangs as a knife, if they don't wanna pay it today, they're not gonna pay it in six months either. And so the same reason they signed up is the same reason they'll keep paying. Here's our description. So the waived fee offers work like this. First, you ask customers to pay a startup fee as a part of joining a month to month program. Typically, you wanna do that to three to five times the monthly rate. All right? So if it was a thousand dollar thing, you'd want it to be a $5,000, uh, front fee. For, you know, the example it was $4,000 a month and $25,000 signup fee. That's the idea. All right. Then you offer a discount on the entire fee if they commit to the longer term. And the commitment period should be minimum of six months, ideally 12 plus. If it's less than that, it doesn't really make any sense. So if they cancel inside the term, they pay the fee. Customers can choose to pay the big fee and keep the option to quit at any time, or they can commit to 12 months and get the fee waived. And many will commit to avoid the big fee. There's also a clear point after four, five, six months where if they paid the fee, it's the same as staying, in which case it basically gets them through that initial churn point, and then after that there's no financial reason to leave the back half of the contract. So we take the greater risk if they pay month to month, but they take a greater risk if they commit. And so if a customer chooses month to month, we lower our risk with the startup fee. But we lower their risk
```

## 10. `situation_sales_team_discounting::payment-plans:8`

**Query:** My sales team keeps discounting when people hesitate. I want a lower-priced option that does not train buyers to wait for a deal. What should we use?

**Query type:** `business_situation`

**Chunk:** `payment-plans:8` from `payment-plans`

**Retriever ranks:** dense-openai rank 5, hybrid-rrf rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | This chunk explains how to frame payment plans to encourage upfront payments, which aligns with the user's goal of providing lower-priced options without encouraging waiting for discounts. |
| Subagent first pass | gpt-5.5 | 1 | Gives seesaw payment-plan tactics for lowering monthly payment without lowering total value, useful but secondary. |

**Chunk text:**

```text
in you, and I think that you can make the best decision. So instead of just asking for the full amount, you say, "Would you rather have giant monthly payments. or tiny ones?" They'll say, "Tiny." Then you say, "Well, it, normally costs XXX, and if you prepay it today, then you get a huge discount and zero monthly payments. That work?" This frames the payment plan as a negative and highlights the benefits of prepay. If they say they can't afford it, say, "The more they put down now, the lower their monthly payments." And so it basically frames all of the payments as, "We wanna make those payments as low as possible, so put more, put more down today. So if you can't afford it up front, totally get it. We'll just adjust the down payment so you get a monthly rate you like." And the thing. is, is that most people want low monthly payments, and so in order to get a monthly rate they like, they have to put more up front. So the seesaw downsell, I call it this because you're just saying, "Okay, well, the more you put down, or the less you put down, the more you have to pay over time. The less you put, uh, the more y- the more you put down, the less you have to pay over time." And so this incentivizes bigger down payments to get monthly payments lower. If they still say no, you ask if they still want the product, just like before. If they do, you pull your chair to their side of the table and walk them through the options. That's how this works. That's the seesaw downsell. It's an alternative path that felt, I felt obligated to at least share with you guys. The thing is, is I like, I think, with larger sales teams, just having very clear step-downs. Sometimes seesaw downselling can get really weird payment plans. And so this is for bigger companies. If you have, like, a finance department, they might hate seesaw downselling because... But if you're owner-operated, then you can, you can kinda work out whatever payment plans work. And it is a more flexible way to make payment plans option, payment plans happen. The seven-step one is more like, it's ironclad. "This is our first stop. This is our second stop. This is our third stop." And then that way, your, your finance team can be like, "These are the plans. They're in the CRM. We track them accordingly," whatever. And so it depends on the size of the business. Seesaws, smaller business, more flexible stuff. The step-downs has more scale to it, in my
```

## 11. `situation_sales_team_discounting::payment-plans:3`

**Query:** My sales team keeps discounting when people hesitate. I want a lower-priced option that does not train buyers to wait for a deal. What should we use?

**Query type:** `business_situation`

**Chunk:** `payment-plans:3` from `payment-plans`

**Retriever ranks:** bm25 rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | This chunk provides a strategy for presenting payment plans that can help avoid discounting while still making the offer appealing, directly addressing the user's concern. |
| Subagent first pass | gpt-5.5 | 1 | Useful payment-term alternatives like credit card or layaway, but not as directly about avoiding discount training as earlier payment-plan chunks. |

**Chunk text:**

```text
how is this third-party financing?" I learned this from a master salesman, so I will just teach it to you as I was taught to me. This is, like, insane close that this works, and it does work, and it still blows my mind that it works. Just ask, "Would you rather that I decide your payment terms or that you decide?" Everyone then says, "Well, I would prefer to decide." And when they do, you just say, "Awesome. Just use your credit card. That way, you can, uh, pick whatever payment plan you want that works for you." If they say, "Well, shoot, what's the alternative to that?" Then you say, "I have an in-house plan, which is me picking the dates of when you gotta pay." And that's usually gonna be a much shorter timeframe than what a credit card would allow you to pay it on. And so as crazy as this is, it's wild to me that this reframe actually works, but it does. So especially if you sell to consumers, like, that reframe works. No idea why. I only state what I know, that it works. All right, the next one is layaway. This is actually a personal favorite of mine. Layaway means paying off the product before getting it. This is actually how they used to do it in the olden days. When there was no credit and banks were all sketchy, people would do layaway. They'd go to the store, they'd say, "Hey, I wanna buy that thing," and the guy would say, "Great, drop off money every Monday for the next four Mondays, and then I'll give it to you." And it was a very simple way. Now, the thing is, is that the customer takes on the risk, not the business. But in my opinion, I think there's a lot of really weird little psychological things with it, because... If you make payments, it's like, it's like building up anticipation for a vacation. It's like the whole time you're like, "Man, I can't wait to get this thing. I can't wait to get this thing." On the flip side, when you get the whole thing and then you make payments, you already got the value and now every time you pay you, like, hate them a little bit more, right? I mean, ideally that's not the case, but I'm just, I'm just explaining my experience as a consumer. Some businesses can't do this. They can't, they can't do a layaway. But if you do have the opportunity or the option where it's, where you can delay starting for a little bit, whether it's a service or it's a product, having them
```

## 12. `situation_sales_team_discounting::payment-plans:2`

**Query:** My sales team keeps discounting when people hesitate. I want a lower-priced option that does not train buyers to wait for a deal. What should we use?

**Query type:** `business_situation`

**Chunk:** `payment-plans:2` from `payment-plans`

**Retriever ranks:** bm25 rank 4, hybrid-rrf rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk discusses payment plans as a way to test pricing but lacks direct relevance to the user's need for a lower-priced option without discounting. |
| Subagent first pass | gpt-5.5 | 2 | Directly shows reframing a higher anchored price into either prepay savings or spread payments, avoiding the feel of discounting after a no. |

**Chunk text:**

```text
purchasing decision. So like, if you had 10 and 20, then yeah. But most interest, or whatever you'd usually, you know, add on top, might be 10, 20%. And so that's not usually enough to get into a different buying tier. So you present here, and if someone says yes, and by the way, if everyone keeps saying yes at that, and then you don't even have to mention the prepay, then it also allows you to incrementally step up and get kind of like, a soft indication in the marketplace whether or not you can sustain a higher price point. So I actually like to use payment plans as a great test for where I'm anchoring, and I can keep nudging up my price before I start seeing people freak out. So it's kind of like a testing price. So I would present 12. They say, "Um, not sure if I can do- it," or maybe they can do it, and then, "Great, wanna save some money?" Now they've pre-paid 10 and they're f- stoked. If they can't do 12, then it's like, fine, oh, you don't have to do it all up front. But now I don't have to increase the price. They said they couldn't do 12, and then I say, "Cool, you wanna spread it over time?" And now it seems like I'm adding no interest to the original price. See how different that feels? Like, oh, you can't do 12? We can break into payments for you. But if, oh, you can't do 10? Then pay me 12. It's like, ee, tough, right? And this gets around all of that. So number two, third-party financing, credit card, and layaway option. So third-party financing means another company pays me now, or pays you now, as a business owner, and the customer has a payment plan with them, the other party. So car dealers do this all the time. The dealer gets money from the financing company today, and the customer pays the financing company tomorrow. Most times, by the way, adding third-party financing in increases revenue by 35%, on average. Note, it does take work to get third-party financing set up, but it is typically worth the effort. Credit cards. Now, you're like, "How is this, how is this third-party financing?" I learned this from a master salesman, so I will just teach it to you as I was taught to me. This is, like, insane close that this works, and it does work, and it still blows my mind that it works. Just ask, "Would you rather that I decide your payment terms or that you decide?" Everyone then says, "Well, I would prefer to
```

## 13. `situation_sales_team_discounting::payment-plans:1`

**Query:** My sales team keeps discounting when people hesitate. I want a lower-priced option that does not train buyers to wait for a deal. What should we use?

**Query type:** `business_situation`

**Chunk:** `payment-plans:1` from `payment-plans`

**Retriever ranks:** hybrid-rrf rank 2

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk provides insights into payment plans but does not directly address the user's concern about discounting. |
| Subagent first pass | gpt-5.5 | 2 | Directly says buyers often need lower payment now, not cheaper stuff, and recommends payment plans that preserve full or higher total price. |

**Chunk text:**

```text
they have to pay you right now, not what they have to pay in, general. And so people mistakenly think that they need cheaper stuff, and this is not the best course of action, in my opinion. Payment plans get the most buyers to pay the highest price by getting them to pay less now in the moment, but pay full price or higher over time. So here are the seven steps of a payment plan downsell. We reward for paying in full rather than punish for paying over time. This is a big thing that I, I don't see taught very much. And so I'm gonna explain this one in depth, 'cause it's really important. Uh, next, we're gonna offer financing options, half now, half later, check to see if they want the thing, offer to split it into three payments, or evenly spread the payments, offer a free trial. So let's give some deep-down examples. So step one, reward for paying in full rather than punish for paying over time. So if I take on the risk of a payment, because if you're a business owner and they don't pay you everything and you start delivering stuff, then you take on risk, right? So then what I do is I increase the price. Now, normally, businesses do this by charging interest. But everybody hates getting charged interest. And so instead, what I do is I anchor... My first price I present is the fully baked payment plan price. And then when I say, "Got it, would you like, to save some money?" they say yes, and I'm like, "You can prepay, and save this much money." So now them pre-paying is a savings rather than getting penalized. So think about it like, this. Let's say it's 10K and 12K. 10K is the pay in full price, 12K is the payment plan price. Instead of s- instead of pitching people, 'cause remember, anchors still work. Instead of pitching people 10 and then they say that no. they can't afford it, and then. saying, "Okay, fine, pay me 12 because you can't afford it," feels tough. So instead, pitch 12, "I know you're afraid of doing it." Don't be. The difference in interest is usually never enough to change a purchasing decision. So like, if you had 10 and 20, then yeah. But most interest, or whatever you'd usually, you know, add on top, might be 10, 20%. And so that's not usually enough to get into a different buying tier. So you present here, and if someone says yes, and by the way, if everyone keeps saying yes at that, and then you don't even have to mention the
```

## 14. `situation_sales_team_discounting::pay-less-now:8`

**Query:** My sales team keeps discounting when people hesitate. I want a lower-priced option that does not train buyers to wait for a deal. What should we use?

**Query type:** `business_situation`

**Chunk:** `pay-less-now:8` from `pay-less-now`

**Retriever ranks:** dense-openai rank 1, hybrid-rrf rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk discusses strategies for encouraging immediate purchases but does not provide a strong connection to the user's specific query about avoiding discounting. |
| Subagent first pass | gpt-5.5 | 2 | Summarizes pay-less-now/pay-more-later as a structured choice with pay-now discount and bonuses, not an ad hoc hesitation discount. |

**Chunk text:**

```text
people in the room. And so I would say, "Hey, people are gonna interrupt me all, you know, to ask about supplements," and then it annoyed me. And I did it one time by accident, and then, of course, it worked really well. And then I started doing it every other time on purpose. All right? And so, by accident, I implied that people who, uh, that everybody bought supplements without actually offering them. And all the head, head nods actually showed that they actually did want more products. And so all these factors got more people to buy when I finally asked them to. So it was a happy mistake that I was sure to repeat. Now, if you're selling over the phone, get the card first. Then ask, "Oh, yeah, I forgot to ask you. Do you wanna save 200 bucks on that price?" So I'm giving you different selling environments. So if you're selling in person, uh, I explained that, the, the lawn care thing. If you sell, uh, digitally, it's a thank you page thing. If you're selling over the phone, you get the card first for the trial. You get the card first for the pay later option. Then you ask, like, the thank you pages once they've agreed to that purchase. Then you say, "By the way, I forgot to mention, do you wanna save a little bit of money?" Or say whatever the price is, "And get these extra things?" A lot of people say yes. And then you just explain, "Yep, so for people who decided to just sign up without, uh, waiting to experience it first, so if you wanna skip the trial, you get VIP seating and recordings from the event, and you get it for $200 less than if you wait. And you won't be able to get those two other bonuses at any time. You wanna go ahead and do that?" And so the more compelling those bonuses are, the more people will say yes. Great. Now, let's summarize this B. All right. So pay less now or pay more later offers people to, uh, a choice to pay full price or pay a discounted price with additional bonuses if they pay now. The pay later option has a delayed payment with a conditional guarantee. Have a clear criteria to qualify for the guarantee and easy ways to measure it. If you can, align the criteria with what gets people the most value from the product. The pay now option offers a 20 to 50%, sometimes two-thirds discount and bonuses if they pay now. It depends how desperate you are to get people to pay. Offer customers the
```

## 15. `situation_sales_team_discounting::pay-less-now:3`

**Query:** My sales team keeps discounting when people hesitate. I want a lower-priced option that does not train buyers to wait for a deal. What should we use?

**Query type:** `business_situation`

**Chunk:** `pay-less-now:3` from `pay-less-now`

**Retriever ranks:** bm25 rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk discusses pricing strategies but does not provide a direct solution to the user's query about avoiding discounting. |
| Subagent first pass | gpt-5.5 | 2 | Gives concrete pay-later versus pay-now examples where the lower price is tied to paying now and added bonuses, not waiting for a deal. |

**Chunk text:**

```text
so you can make three times the amount. All right. And so you can charge more. for the thing. since a delayed purchase to the same degree. People will agree to pay more later than they will now. And so you can also boost the price because also if so- you... If someone... It basically means what's the price of the guaranteed delivery. So when you have someone pay today, there's a, a risk metric that, they apply to the purchase on. the risk that' they don't get what they think they're going to get. If I said, "Hey, you only pay me after you get a six-pack," then people are like, "Oh," then the value of a six-pack is directly related to the price that they pay, which means I could charge way more for that thing because it's at a delay. And so we wanna give the one-time offer, uh, of the same thing for one-third to one-half the price, plus bonuses and guarantee to get more people to buy now. Great. All right. So let's do some examples, 'cause some people are like, "Okay, I get how it, work for the reading story, but how does it work for other businesses?" So pay later, zero plus 299 after three-hour training. Pay now, 149, 97, doesn't matter. Recording plus notes. Okay, now some of you are like, "Wait, I thought you said 20 to 50. I thought you said 67." Doesn't really matter. You just pick the discount amount that accomplishes your objective for offsetting as much cash as you need to break even on the acquisition. Now, upsell,And also to be clear, if you are doing this, this thing is happening all within 30 days, I also include the cash I get from the pay later, option, because they're still paying in that 30-day window. So if I get some today and then some in two weeks or some in three weeks or some in four weeks, I still get it before I pay my card back. Whatever, doesn't matter to me. Now, upsell. The upsell here is the eight-week double your reading speed thing. Cool? So we have three offers. Pay later, pay now, upsell. That's how this works. Now, let's say I'm in the, you know, find your first real estate deal. Okay, fine, I do a three-day workshop. Pay later for zero dollars for a three-day workshop. They get billed $500 at the end, unless they cancel. Pay now. is $299 for the three-day workshop, plus the recordings, plus a one-on-one call with a distressed property expert, plus printed materials that they can use at the workshop. Kind of compelling. Now, the upsell is
```

## 16. `situation_saas_onboarding_commitment::waived-fee:3`

**Query:** Our software has setup work, but if we charge a setup fee fewer people start. If we waive it, people churn fast. Is there a way to create commitment without scaring them off?

**Query type:** `business_situation`

**Chunk:** `waived-fee:3` from `waived-fee`

**Retriever ranks:** bm25 rank 5, dense-openai rank 5, hybrid-rrf rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk provides some useful context about fee structures but is less focused on commitment strategies compared to others. |
| Subagent first pass | gpt-5.5 | 2 | Directly provides example pricing and variables for waiving a setup fee in exchange for a commitment. |

**Chunk text:**

```text
thousand dollars a month, fee is $5,000 if they pay month to month. Option A, pay one time five grand plus a thousand dollars for the first month, then pay $1,000 a month thereafter, cancel whenever you want. Option B, waive the $5,000 if you commit to 12, pay $1,000 per month, only pay the $5,000 fee if you break your commitment early. Boom. Very simple, very straightforward. There's the visual. If you want, you can do a different version of this where you keep, uh, the month to month rate higher. So if they cancel, the discounted commitment, you bill the difference. All right? So let's say, uh, they, basically the longer they stay, the bigger the cancellation rate. So if they've accrued, you know, uh, $177 of savings or $67 of savings every single month on their commitment, the day they wanna, they wanna break the contract, they pay the difference in savings up to that point. Now let's do some important points. So four variables for this method. You've got the commitment length, you've got the commitment rate, you've got the month to month rate, and you've got the fee that they're gonna waive or not. There are more versions of this beyond the two that I shared. You can figure them out on your own. Now, I had an earlier version of this that had like nine different versions and my editor was like, "You're honestly just gonna confuse people, so don't do that." So fundamentally though, you can mix and match these however you want. You can have a, like the rate difference between the people who commit can be less. You can have, uh, the length be a variable. Uh, the rate that you charge month to month is different, the fee that you waive. So all of those things kind of go into this deal structure. The recommendation that I have is a model that works, which is take the price, multiply it by five, make that the fee, waive it-And that holds, that basically hangs over their head the whole time. And if you want, again, the ethical reason for this is that many businesses and many services have emotional ups and downs. They're volatility for customers. And so having something kind of like guardrails to keep someone on point during the rough months can help them overall see success. And I believe that. So that's not just not, that's not just wordsmithing. That's true. Um, and this vehicle or pricing structure, money model, allows you to build incentives around that. All right. So fees get them to start. People get value out of committing immediately because they avoid a fee. People
```

## 17. `situation_saas_onboarding_commitment::waived-fee:1`

**Query:** Our software has setup work, but if we charge a setup fee fewer people start. If we waive it, people churn fast. Is there a way to create commitment without scaring them off?

**Query type:** `business_situation`

**Chunk:** `waived-fee:1` from `waived-fee`

**Retriever ranks:** bm25 rank 3, dense-openai rank 3, hybrid-rrf rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk offers background on the waived fee structure but lacks depth in addressing commitment strategies directly. |
| Subagent first pass | gpt-5.5 | 2 | Directly defines the waived-fee commitment offer and matches the setup-fee versus churn tradeoff in the query. |

**Chunk text:**

```text
a one thou- you know, a thousand dollar a month continuity plan, right? You could say, "Cool, this is 5,000 down, then a thousand bucks month to month. Or I will waive the $5,000 fee and it will be free with a 12-month commitment at $1,000 a month, and you pay that if you wanna cancel early." So this is fundamentally a neat cancellation term. Fundamentally it's, what it' is, but because we pair it as a price on the front end, it becomes a very strong sales thing too. So with the other version, we use the three, months free or whatever to get someone in, and then we say, "Cool, you have to pay the difference if you cancel early." Here, we sell them on the vacation and we say, "We have this massive onboarding fee, but I'll waive it if you sign up for a commitment." Then that' also hangs as a knife, if they don't wanna pay it today, they're not gonna pay it in six months either. And so the same reason they signed up is the same reason they'll keep paying. Here's our description. So the waived fee offers work like this. First, you ask customers to pay a startup fee as a part of joining a month to month program. Typically, you wanna do that to three to five times the monthly rate. All right? So if it was a thousand dollar thing, you'd want it to be a $5,000, uh, front fee. For, you know, the example it was $4,000 a month and $25,000 signup fee. That's the idea. All right. Then you offer a discount on the entire fee if they commit to the longer term. And the commitment period should be minimum of six months, ideally 12 plus. If it's less than that, it doesn't really make any sense. So if they cancel inside the term, they pay the fee. Customers can choose to pay the big fee and keep the option to quit at any time, or they can commit to 12 months and get the fee waived. And many will commit to avoid the big fee. There's also a clear point after four, five, six months where if they paid the fee, it's the same as staying, in which case it basically gets them through that initial churn point, and then after that there's no financial reason to leave the back half of the contract. So we take the greater risk if they pay month to month, but they take a greater risk if they commit. And so if a customer chooses month to month, we lower our risk with the startup fee. But we lower their risk
```

## 18. `situation_premium_option_makes_core_sell::classic-upsell:4`

**Query:** I think a small percent of buyers would pay way more for done-for-you help, and even if they do not buy it, I want the normal offer to feel more reasonable. How should I frame that?

**Query type:** `business_situation`

**Chunk:** `classic-upsell:4` from `classic-upsell`

**Retriever ranks:** bm25 rank 4, hybrid-rrf rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | This chunk provides a detailed explanation of upselling strategies, emphasizing the importance of making upsells feel essential, which aligns with the user's goal of framing a premium offer. |
| Subagent first pass | gpt-5.5 | 1 | Adjacent upsell guidance for done-for-you add-ons, but not the anchor framing that makes the core offer reasonable. |

**Chunk text:**

```text
## [§4.2.e] Important points + 80% close rate benchmark

So important points, so number one, if you make thing A free, then you gotta be able to give it away for free. If someone comes in and wants the free workouts, you have to deliver the free workouts. Now, you can't say, "You have to buy this other thing, otherwise it's not free." You wanna strongly encourage the thing, but that's fundamentally how it works. All right? So make sure that it doesn't cost you a lot or anything at all, uh, like, that thumb drive that we gave, like, you can y- you want it to be something that's cheap, uh, but still valuable. The next thing is make the upsells the next natural thing that they would need to buy. That's the boxes, the large units, the locks, the, the insurance, things like, that. The weight loss clinic, continuity of service, continuity of supplements, done-for-you meals, hormone treatments, et cetera, all of those things were all part of classic upsells that' went through. You can't have X without Y. You can't have this weight loss service without these supplements. Just think, "You can't have X without Y," as your, as your mental framework for what the next thing I'm gonna offer is. All right, this play works so, well because the perception of how essential or required the next thing is. All right? So, this is the key point. If supplements is core to how someone's gonna get results with the main thing, the likelihood they buy is very high. So, if you, remember the, uh, minimum package for the rental car story I gave you, you want this to, feel as required as possible. Again, you don't wanna make it' required, because then it's, it's, it gets shady, but you want to strongly encourage people to take these things to get the best results, which ethically, they should be able to get better results with whatever your upsell is. All right? And so, how seamless the upsell process is for the prospect, if you make it frictionless, you can get sometimes 80% plus the people to take these upsells. I personally prefer to have upsells that have very little operational drag so, that I can' immediately offset cost to get it, getting a customer, or it becomes that's my major profit stream. It depends on' what the objective is for your business. Boom. Summary, works on' the front end as a back end, works as an internal play, meaning you can just upsell your existing customers. That's basically what the storage thing with, with the fur coats was. Many of those people were existing customers, so you can just upsell those people. Um, if you suck at sales, this is not a hard sale to make. Uh, there's a lot of goodwill in this play, because you just make sure that you close the upsell. Like, it's like, "Hey, let me give you this thing. I'm giving you this free earmuffs. Why not take it? But, of course, you gotta take this other thing, too." Um, and if you aren't getting 80% plus close rates, you're doing it wrong. So that's my big benchmark for you. If you're getting 30% to take it, you're not, you're not making it assumed enough. You're not, it's, it's not clear enough to them that this goes with. So think about it like that. It has to go with. If you go to a McDonald's, I would bet you that 80% of people are getting fries and a Coke. You want, you want a very high uptake rate on' the people who buy the next natural thing. Think of this as the thing that goes with the thing, uh, and give the thing away for free to make sure that all the thing that goes with the thing you can make the money on. All right? And so, the nice thing with this is that it gives you a lot of upfront customers. And that is the classic upsell.
```

## 19. `situation_premium_option_makes_core_sell::buy-x-get-y:6`

**Query:** I think a small percent of buyers would pay way more for done-for-you help, and even if they do not buy it, I want the normal offer to feel more reasonable. How should I frame that?

**Query type:** `business_situation`

**Chunk:** `buy-x-get-y:6` from `buy-x-get-y`

**Retriever ranks:** hybrid-rrf rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk provides context on prepayments and upselling, but does not directly address how to frame a premium offer. |
| Subagent first pass | gpt-5.5 | 0 | Buy-X-get-Y/prepayment guidance, not presenting a premium option to anchor the core offer. |

**Chunk text:**

```text
for fast cash. Now, if your business is healthy but you're like, "You know. what? I wanna buy a bunch of equipment," great. Prepay 10 people, go buy your equipment. Or you need to go buy a, uh, another big oven, industrial oven for your baking business. Like, totally makes sense for you to do prepayments and things like that to cash flow or fund rather than take on credit lines. Super smart. Um, so, even if customers prepay, you can still upsell them different stuff now. So this is really important. So I made this mistake, which is why I share it with you. The people who prepay, especially for services, for durations of time, business owners have this fear of selling them or making offers for other stuff. But here's the craziest thing that we saw, is that the people who prepay for the year are the most likely people to buy more stuff afterwards. And so these are basically a way of identifying your hyper buyers. And so they self-select. They prepay for a year, and guess what happens after that? When I would have Big Booty Boot Camp and a deadlift seminar or, you know, uh, Make Your Sexy Back or I would do Buns & Guns or whatever else I would do, Lean by Halloween, they were the most likely people to pay, 'cause guess what? They weren't paying anything for being there as far as they felt. They, they had paid so long ago they forgot that they paid. So it felt like I was just a free gym. And you know what? The cool thing about wallets with people who make money, they replenish and then you can ask again. So if customers only buy once, this is just a disclaimer for the, um, for the boot business. The reason they structured their deal that way was to maximize the transaction. So if you're in a business where people only buy once, then it makes sense to structure as much into that first sale as you can 'cause you're only gonna get one shot. Like the bachelorette parties are probably not coming back to Nashville. Now maybe they will, but for the most part, that's this... You wanna make the big, the ask as big as you can if you're only gonna get one shot. Summarizing buy X, get Y, free. In buy X, get Y free, customers buy something, they get other stuff for free. Buy X, get Y free. works, uh, for stuff that makes sense to buy more of or get longer access to. Basic buy X, get Y free, offers reframe pricing. Buy one, get two free, costs the
```

## 20. `situation_premium_option_makes_core_sell::buy-x-get-y:4`

**Query:** I think a small percent of buyers would pay way more for done-for-you help, and even if they do not buy it, I want the normal offer to feel more reasonable. How should I frame that?

**Query type:** `business_situation`

**Chunk:** `buy-x-get-y:4` from `buy-x-get-y`

**Retriever ranks:** dense-openai rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk provides insights on structuring offers but does not specifically address how to frame a premium offer. |
| Subagent first pass | gpt-5.5 | 0 | Generic free-items-versus-discount framing, not anchor upsell. |

**Chunk text:**

```text
wrinkle and that's very high margin for me. So for a gym, I'd- I might say, "You get text access to me," which by the way, I probably would give all my first customers anyways. I just wouldn't promise that in the sale. I might for a grand opening. So raise prices when we're giving stuff away to preserve profits. Obviously, if you can only afford a certain amount of margin, then don't give away your margin. That's just like my big obvious disclaimer. Now buy X, get Y free works better if you have more free stuff than paid stuff. All right? So giveaway, give more free than you ask people to buy. Just play with the pricing until it makes sense for you. So buy one, get two instead of buy two to get one. So these are the same economics, but this one's stronger. That's how it works. Okay. Now, the free things can be different from the paid things. So this is key. So you just wanna make sure that the free stuff still makes the offer compelling. Let's say that, uh, socks have a $10 value. If they buy one shirt for 10 bucks but get $20 of free socks, it may seem like a better deal. Now alternatively, here if we're looking at like buy one sh- let's say shirts are 20 bucks. If I say buy one shirt for 20 and get another shirt free, that may seem like less valuable than buy one shirt, get two pairs of socks free, because what someone's gonna translate it into is buy one thing, get two things free versus buy one thing, get one thing free. Now this is a testable proposition. In some, some offers, two pairs of socks may convert better than one shirt, depending on if the way that that buyer buys, the next logical thing they would need would be socks. So more free cheaper things can work better than fewer free expensive things. Okay? So let's say I could only afford to give one shirt away for free, but now the same, for the same cost, I give three pairs of socks. I would probably test buy one shirt, get one shirt versus buy one shirt, get three socks for free. And even though the socks cost less than a shirt, it's still buy one, get three. And sometimes that converts better, so I test this. Rather than offer a 33% discount, try buy one, get two free. This here will convert more than this, but they're still one thirds off. All right? So I just like to... If you are gonna use a discount, this structure still makes a
```

## 21. `exact_free_with_consumption::decoy-offers:3`

**Query:** What is a free-with-consumption offer?

**Query type:** `exact_framework`

**Chunk:** `decoy-offers:3` from `decoy-offers`

**Retriever ranks:** bm25 rank 2, dense-openai rank 5, hybrid-rrf rank 1

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 0 | The chunk discusses decoy offers but does not define or explain free-with-consumption offers. |
| Subagent first pass | gpt-5.5 | 0 | Defines and exemplifies decoy offers, not free-with-consumption offers. |

**Chunk text:**

```text
of the bonuses from the premium and toss them in because you're like, "Hey, I know you're only taking the, the one workout a week thing, but let me do some personal nutrition for you. Come back in a week or come back in two days." And guess what we do at the personal nutrition consult today? Sell them $300 of supplements. Right? And so it's, it's all good. All right? But either way, here's the thing is you close everyone, and this makes it cheap and profitable to get new customers. And any business can do this. You literally just take what you have. Well, I'll get into what it is. Okay. So here are the steps to make a decoy offer. One, advertise a lesser, smaller, or simpler version of your premium offer as the decoy offer. Then, when leads engage, offer both options, but emphasize the premium one. And use the bonuses, the premium value, and the guarantees to close the additional people. All right. Now, let's do some examples. So let's say I have a lemonade stand. This is to prove the point that it works with literally any business. All right, so you, the attraction offer is, uh, this is, like, what the headline of the ad might be. So you'd say, "Hey, free week of lemonade for all first-time customers." Okay? Now, I'm not giving any features. I just said, "Free week of lemonade."Now, option A, this is the free week, is that you can have this free plus water and powder, uh, this warm water, right? And artificially sweetened and it may give you digestive issues, uh, but you can absolutely have this free lemonade or you could have the organic, all natural, vegan, gluten-free imported Italian lemons which are cold distilled and shipped straight to your door so you never waste time coming into the store. And so it's like, which one do you want? Right? Of course you want this one. You want the premium one. And so that's what people take. So let's say you've got, um... This is actually a, so a float tank center. I had an agency that did float tank stuff for a minute, uh, in Allen. So they used a free six-week stress release challenge. Okay, so the attraction offer was a free six-week stress release, uh, or, um, as... you could say a $6 six-week stress release. Either way, that free or discount. Decoy option, you get one float per month with at home do it yourself stress relief exercises or premium option is two a week floats for six weeks, one-on-one consulting, journal, sleep routine, and a satisfaction guarantee. Guess what everyone took?
```

## 22. `exact_free_with_consumption::buy-x-get-y:1`

**Query:** What is a free-with-consumption offer?

**Query type:** `exact_framework`

**Chunk:** `buy-x-get-y:1` from `buy-x-get-y`

**Retriever ranks:** dense-openai rank 2

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 0 | This chunk focuses on buy X get Y offers and does not provide relevant information about free-with-consumption offers. |
| Subagent first pass | gpt-5.5 | 0 | Defines buy-X-get-Y-free mechanics, a different offer type. |

**Chunk text:**

```text
to college out of high school knowing literally nothing about anything, I assumed that I was more intelligent than the store owner who obviously was doing very well. And so, uh, I came back 10 years later, and they had expanded. And so I was like, "Huh, that's interesting." Now, 10 years later, I had a lot more business. acumen. And so I went in, and I, like, looked around poked around, and I saw that the pairs of boots had... each of them had multiple markdowns on the price down to $600 for one pair, at least the ones that I looked at. And so it was... instead of saying, "Buy one fairly priced boots," or, "Buy 20% off," they had, "Buy one, get two free." But if you bought three pairs of boots for $200 each, that's still, like, a pretty normal price for leather boots. And so the ones that I... like the ones I was looking at were not like Stingray or, you know, Hippopotamus or something like. They were, they were normal leather. And so I realized that they had just fully baked the cost of three into one pair and then said, "Buy one, get two free." And the thing is, is that because of that, all the bachelorette parties would pile in because the bride would get one, and then the other two friends would get them for free. Or one of the friends would buy a pair and give one to the bride and one to her maid of honor or whatever, and they just milked it. And so that is how I learned this more valuable way of doing buy X get Y free. So let's get into it. So in buy X get Y free offers, customers buy something to get other stuff free. Cool. Makes sense. The more free stuff they get and the higher its value, the better it works. Buy one get two free works better than buy two get one free. Free offers get way more attention than discount offers. But if you only have one thing to sell and give it away, then obviously, you go hungry. If you just say, like, "Buy... Here's free boots," that's not gonna work, right? So in situations like this, they tend to lean on discounts. All right? Most businesses do. So they run sales relying on holidays, seasonal changes, or whatever, as, you know, reasons to temporarily lower the price for whatever the thing is to get more customers. But by selling more than one thing at once, you can turn discount offers into even stronger free offers. This is the magic of buy X get Y free.
```

## 23. `exact_free_with_consumption::buy-x-get-y:7`

**Query:** What is a free-with-consumption offer?

**Query type:** `exact_framework`

**Chunk:** `buy-x-get-y:7` from `buy-x-get-y`

**Retriever ranks:** dense-openai rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 0 | The content is about buy X get Y offers and does not relate to free-with-consumption offers. |
| Subagent first pass | gpt-5.5 | 0 | Summarizes buy-X-get-Y-free, not free-with-consumption. |

**Chunk text:**

```text
as big as you can if you're only gonna get one shot. Summarizing buy X, get Y, free. In buy X, get Y free, customers buy something, they get other stuff for free. Buy X, get Y free. works, uh, for stuff that makes sense to buy more of or get longer access to. Basic buy X, get Y free, offers reframe pricing. Buy one, get two free, costs the same as buying three except customers see the free offer. as more valuable. Remember the 18-month service example I gave. So always try to give more free things than paid things and you can pair different free things with paid things as well, which you can just test. All right. So buy X, get Y free can lengthen the amount of time customers stay. If normal customers stay for three, months, then buy two, get two customers will keep them for four months. So whatever you sell, try and extend whatever the normal customer duration is by saying, saying like, "If I know customers stay for three, I do buy two, get two and I price it' so that it's still four, I make more money. I make 33% more money." It's a great deal. Uh, if you use buy X, get Y to generate a lot of cash fast, make sure you manage it. and you can deliver on your promises. If you need fast cash and your business is healthy, make sure, make this offer to existing customers, uh, and just cap how many you sell it to. If you have recurring, I recommend 10% is the cap. Um, keep selling customers who prepay for long durations because they are the most likely people to buy again. With that being said, that is buy X, get Y free.
```

## 24. `exact_free_with_consumption::decoy-offers:2`

**Query:** What is a free-with-consumption offer?

**Query type:** `exact_framework`

**Chunk:** `decoy-offers:2` from `decoy-offers`

**Retriever ranks:** bm25 rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 0 | This chunk discusses decoy offers and upselling, not free-with-consumption offers. |
| Subagent first pass | gpt-5.5 | 0 | Explains decoy offers and premium upsells, not the free-with-consumption structure. |

**Chunk text:**

```text
those two offers, they came in for the free 21-day transformation. But when they were presented the premium version, they said, "You know what? I'd rather do that." Upselling is as American as apple pie. There is nothing wrong with having an upsell as long as you still offer something that is free that complies with what your original promise was in the advertisement. So if someone comes in... And the key point of making this work is that you can advertise the free 21-day transformation, not also you get all this stuff. If you say you get this other stuff too, then you have to deliver on it. And so the key is, and this is one of the benefits of advertising results rather than the, the vehicle, because then you can choose the vehicle and associate price however you want in the sales presentation. All right? And so this offer structure, right, this money model is 100% based on the upsell. This is how all of the money of this works. And the key, if you have the structure properly, is 70 to 80% of people should take the premium version. So description. So decoy offers advertise something free or discounted. So I could just as easily say, "$19 or $21 21-day transformation." They come in, and they say, "Cool, you can do the $21 one. You already paid for it. Or I'll credit your $21 towards a $421 thing, which we'll roll it towards, and now you can pay an extra 400 bucks today, and you're in," right? So then, when leads ask to learn more, you also present the more valuable premium offer. And the premium offer provides more features, benefits, a bonus, guarantees, and so on. So by putting your decoy offer and premium offers next to each other, they can see how much more valuable your premium offer is. And so I like, decoy offers so much because they get more customers overall. And so they either take the decoy version, or they get the premium version. This is an assumed close. That means everybody buys. I like, that. Now, if they take the premium version, great. If they take the decoy offer, also great. And guess what? You can also grab a couple of the bonuses from the premium and toss them in because you're like, "Hey, I know you're only taking the, the one workout a week thing, but let me do some personal nutrition for you. Come back in a week or come back in two days." And guess what we do at the personal nutrition consult today? Sell them $300 of supplements. Right? And so it's, it's all good. All
```

## 25. `exact_free_with_consumption::decoy-offers:5`

**Query:** What is a free-with-consumption offer?

**Query type:** `exact_framework`

**Chunk:** `decoy-offers:5` from `decoy-offers`

**Retriever ranks:** bm25 rank 5, hybrid-rrf rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 0 | The chunk is about decoy offers and does not address free-with-consumption offers. |
| Subagent first pass | gpt-5.5 | 0 | Gives decoy-offer sequencing details, not a definition of free-with-consumption. |

**Chunk text:**

```text
one year for $900, 1200 bucks. All different ways of saying the same thing. So these are all useful, especially with decoy offers 'cause oftentimes they are discounts. All right. So the key to making this work is that the contrast has to be huge. All right? The bigger the contrast, the better the deal, the more customers will take it. If people keep taking your free offer, your free offer is too good and your paid offer is not good enough. So you want to keep doing this until the obvious offer is to take the premium offer. All right? Discount offers have high upshare rates than free offers. Just as a pro tip, if you do have these issues, you can do the $21 thing if you have sharp rate issues in your market. If possible, present the premium offer first. Now, if they ask for the decoy offer, most people don't, you then present it. But I'll show you how to do this. Okay? So what you wanna do is get them to give you permission to sell them. So if they asked to peer about the decoy, then you're legally obligated to present it. On the other hand, some of you guys might be a little bit weak in the stomach about just offering something straight for the, the h- high value thing. But here's... Let me just share a little bit of, like, advertising scars and, like, years of doing this. Almost no one remembers what they opted in for. They barely remember the ad. And so they just f-... They will remember that this thing solved the problem that they have. And then when you... they come in, you can just make the offer that you wanna make them. Now, if they do remember that thing, then by, all means tell them about it. But if you are somebody who's like, "I want to always offer the, really cheap thing first," fine. This works in the opposite way, of price anchoring, but fine. Have it. your way. So if you're gonna do it' that way, here's how you' do it. So you ask them a sorting question first. You say, "Are you here for free stuff or lasting results?" Everybody's gonna say lasting results. Some people will say free stuff and those people suck and you can just kick 'em out basically. Um, but as soon as they say results, which most people do, you skip straight to premium. So this way you've gotten permission to then sell them the premium offer. Now, if they say free, then you say the free thing and then you present the premium. So this way you can
```

## 26. `diagnostic_low_first_month_gp::cac:1`

**Query:** CAC is $350. The first purchase produces $120 gross profit and then $40 gross profit per month after that. What is the bottleneck?

**Query type:** `diagnostic_numeric`

**Chunk:** `cac:1` from `cac`

**Retriever ranks:** dense-openai rank 1

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 0 | This chunk discusses CAC calculation but does not provide relevant insights for identifying a bottleneck in the context of the user's specific query. |
| Subagent first pass | gpt-5.5 | 1 | Useful for calculating CAC, but it does not diagnose the low first-month gross profit bottleneck. |

**Chunk text:**

```text
business owner. So this is how we, this is how we calculate it. So the total cost for eight sales means that you have a $3,000 emailer plus a $200 software plus 800 bucks in commissions, which is eight sales times $100 equals four grand. All right? So now, we divide that by the number of new customers, which is $4,000 divided by eight new customers equals 500 bucks per sale. So CAC. is $500 in this outreach example. So let's say that you have a content business. So let's do this one. So you have to pay two people on your media team that you pay $5,000 a month each, and they help you make, edit and distribute content across all platforms, right? So that content then turn into inbound messages and then opt-ins on your site, and then those leads turn into 10 new customers and you pay $100 in commission per sale. All right. So what's CAC? So the reason I'm giving you all those stats is so that you can plug your own stats in and then figure this out for yourself. So if my media payroll is 5K times two, it's $10,000 a month there, my commissions is 10 sales times 100 is 1,000. So all in I got 10 grand plus one grand is $11,000. So my cost to acquire a customer we'll say is $11,000 divided by 10 customers equals $1,100. So my CAC's 1100 bucks. Now if some of you are like, "Wait, I have sales payroll in there too," then add it in. If there's something that you don't have here, cut it out. But fundamentally it's just all the money you spend to get new customers divided by how many customers you got. Cool. And I'll do one quick one on paid ads. So you spend $4,000 a month on a media buyer, you spend 20 grand in buying ads, the actual media itself. You spend 1,000 bucks commissions per sale, so this is probably a higher ticket sale, and you spend $1,000 on software and tracking and following up with leads that come in to get 10 new customers. So what's CAC? So media, 4K, media spend, 20K, software, 1K, commissions, 10 times one, 10,000. So all in, we spent $35,000 divided by 10 customers, $3,500 per customer is our CAC. That's how this works. By the way, one of the best ways to improve any metric is to start measuring it. So, how to improve it? In this whole training, I talk about lots of different things that cover and check off different boxes here. But fundamentally, if you had nothing else and you just wanted to have
```

## 27. `diagnostic_low_first_month_gp::cac:0`

**Query:** CAC is $350. The first purchase produces $120 gross profit and then $40 gross profit per month after that. What is the bottleneck?

**Query type:** `diagnostic_numeric`

**Chunk:** `cac:0` from `cac`

**Retriever ranks:** dense-openai rank 2

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk provides a definition of CAC and discusses its components, which is partially useful for understanding the context but does not directly address the bottleneck. |
| Subagent first pass | gpt-5.5 | 1 | Defines CAC and acquisition cost inputs, which is background for the question but not the bottleneck answer. |

**Chunk text:**

```text
So, cost to acquire a customer, AKA CAC. Let's dive in. Cost to acquire a customer, again. So, let's start with definition. All right, cost to acquire a customer, all the costs required to sell a new customer, so, that's the advertising dollars, the payroll to a media buyer, creative team, software that you, that the team uses to make advertising and sales commissions, salaries, the managers of those teams, everything that it costs you. So, a lot of people... And if you want, you can delineate how much does it cost if you use paid ads, for example, how much it costs us in media spend versus how much is our, sometimes people call it fully loaded CAC. Uh, you can have both those numbers separated out, which I think is wise, kind of like media CAC versus fully loaded. Uh, but at' the very basics now, that only really applies to paid media. If you, acquire customers via outbound, payroll is gonna be the majority of your CAC. If you. use, uh, content to get customers as your primary acquisition, uh, method, then it's just gonna be the cost of the payroll for the team that does all the distribution of content and editing and whatnot. But most companies, especially if you're bigger, are gonna have multiple different versions of that, which is why you just look at everything and you look at how many customers you got, you divide it out and you're like, "That's our, cost per customer." So if we're trying to get unlimited customers, we better be sure we know what our ca- own costs, uh, to make sure that we can actually pay for it so that we can get unlimited new customers. All right, so let's calculate it together. So if you use outreach as your primary way of getting customers, then you use, let's say, $200 a month in email software and you pay someone $3,000 a month to do cold email prospecting for you, then emails become appointments that turn into eight sales per month. And so then you pay your salesperson $100 per sale. So then what's CAC, right? This is like a ChatGPT prompt word problem. But fundamentally, this is what it looks like for you as a business owner. So this is how we, this is how we calculate it. So the total cost for eight sales means that you have a $3,000 emailer plus a $200 software plus 800 bucks in commissions, which is eight sales times $100 equals four grand. All right? So now, we divide that by the number of new customers, which is $4,000 divided by eight new customers equals 500 bucks per
```

## 28. `diagnostic_low_first_month_gp::gross-profit:5`

**Query:** CAC is $350. The first purchase produces $120 gross profit and then $40 gross profit per month after that. What is the bottleneck?

**Query type:** `diagnostic_numeric`

**Chunk:** `gross-profit:5` from `gross-profit`

**Retriever ranks:** dense-openai rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk discusses ways to improve gross profit, which is relevant but does not directly identify the bottleneck in the user's scenario. |
| Subagent first pass | gpt-5.5 | 1 | Partially useful because it lists ways to improve gross profit, but it does not diagnose payback or CFA from the numbers. |

**Chunk text:**

```text
your rent doesn't go up per unit sold, if your admin cost doesn't go up per unit sold, then it is not factored into gross profit. But if my hard cost of cups, if I sell another cup, I still have to incur that cost. If I, if I have, uh, if I have to sell another client, then a certain portion of my resources of client delivery is gonna get allocated to that next client. Now some people are like, "Wait, but I have to pay my person either way." Not really. I mean, you do up to 20, and then you have to hire another one. And so you just have to fractionalize it in terms that you're thinking. So it may feel fixed, but it's not. You just have to, you have chunkier, um, start/stops more than it's, uh, a fixed cost, if that makes sense, when it comes to calculating this. So you're like, "Okay, got it. I have mine and mine sucks, so what do I do to improve it?" So improving gross profit, there's a lot of ways to increase gross profits. Um, but without altering price or cost structure, the three easiest to remember are more, better, new, all right, which is sell more of the stuff, so more quantity or duration of the thing. So get them to buy in bulk or buy again tomorrow. Sell a better quality version of the thing. So that would be like a regular burger versus an organic burger, or a large group versus personal training, better version of the thing. Or sell a new thing, so you, fries and a Coke, which then you could supersize on quantity and quality as- on top of that. That's the, that's the quick and dirty. We're gonna get into lots of different versions of this. All right, so that is gross profit.
```

## 29. `diagnostic_low_first_month_gp::gross-profit:3`

**Query:** CAC is $350. The first purchase produces $120 gross profit and then $40 gross profit per month after that. What is the bottleneck?

**Query type:** `diagnostic_numeric`

**Chunk:** `gross-profit:3` from `gross-profit`

**Retriever ranks:** hybrid-rrf rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | This chunk explains gross profit calculation and its importance, which is relevant but does not directly address the bottleneck. |
| Subagent first pass | gpt-5.5 | 1 | Explains gross-profit calculation and service margins, useful background but not the specific first-month payback diagnosis. |

**Chunk text:**

```text
of attention, he would outbid me every time. And our goal is to do the same to our competitors. All right? So you need to look at both sides, getting customers for less, but also making them worth more. All right? And before we improve it, we gotta know how to calculate it. So here's gross profit, how we calculate it. So here's a product example. So if I sell a widget for $100, it costs me 20 bucks to manufacture it and ship the widget to the end customer. All right? So my gross profit is 100, where it is, 100 minus 20, 80 bucks. This is what's left over. This is my gross profit. Okay. Here's a service example. Let's say I deliver services monthly and I have one account representative per ten customers. If my clients pay me $3,000 per month each and my reps cost me $6,000 per month, we can then figure out the gross profit margin. Okay.So the rep salary is six thousand dollars. The clients per rep is ten. The cost per client means it's six hundred dollars per client. Remember, we make six thousand dollars, divided by ten clients, six hundred dollars per client. Gross profit, all right, is now three thousand dollars, what they' pay us, minus my cost per client, which means twenty-four hundred left over. The reason I'm going through this is that many of you, guys watching this are service-based businesses and don't know your costs. These, are your costs. So my gross margins are twenty-four hundred divided by three thousand dollars, which is 80%. Rule of thumb from Alex, if you run a service-based business, local brick and mortar or national, you want at least an 80% gross profit margin. Now that- that may sound crazy to you, but it is very unlikely that you will scale in service unless you have 80 or higher. So not just eight- that means that if it cost you a hundred, you gotta sell it for five hundred. Now you might think, 'cause if you're a newer business owner, you're like, "No, I- that's- that seems unreasonable." That's your gross profit, not your net profit. You still have rent. You've got, you've got your fixed admin cost, you've got insurance, you've got utilities, you've got break-fix that happens within your business. You've got all these other costs that go into doing business. You're not running 80% net margins. You're just saying this is now all the money I have left over to run the re- I still gotta spend advertising dollars. Like there's all this money that I still gotta spend. And so if you're- if you're at 80, you
```

## 30. `diagnostic_low_first_month_gp::cfa:1`

**Query:** CAC is $350. The first purchase produces $120 gross profit and then $40 gross profit per month after that. What is the bottleneck?

**Query type:** `diagnostic_numeric`

**Chunk:** `cfa:1` from `cfa`

**Retriever ranks:** bm25 rank 3, hybrid-rrf rank 2

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | This chunk discusses the importance of having gross profit greater than CAC within the first 30 days, which directly relates to identifying the bottleneck in the user's query. |
| Subagent first pass | gpt-5.5 | 2 | Directly states that first-30-day gross profit must exceed CAC for level two; the query's $120 is far below $350. |

**Chunk text:**

```text
owned everything, and I haven't sold equity, and I haven't taken on debt to grow all my businesses, and I've been able to grow them absurdly fast relative to the marketplace. I'll just say it like that. And the way that we've been able to do it is because I take the money that I have access to, and I can take as much as I possibly can as long as I figure out a, way to pay it back in that first month. All right? And so you can use the credit card to get your customers, then pay the card back, then reuse the money, recycle the cash, and get another customer. All right? As long as your gross profit in the first 30 days is greater than the cost to get them, you can never carry debt while growing your business, which is a sizeable advantage. So, this is what level two advertising. would look like. So 30 days' gross profit. So that means that, like, if I got that first customer, right, if it cost me, uh, 160 to get the customer, and I got 180 back in gross profit, then it's just all free. They're all... It's just all free. That's how it works. And so note is that if you have an XXX limit on your credit card, you'll always be limited by the amount of customers that XXX number buys you before having to pay it back. And so this assumes that you don't reinvest the excess profits after the 30 days on marketing rather than putting it in your pocket. Okay? So once you unlock acquisition this way, typically, you will get limited by your operational constraints before you will get limited by your advertising constraints. You will not be able to handle the amount of customers that you can bring in, and that's what's going to throttle down your advertising more than you can't get more customers. So that's level two is that now your 30-day gross profit is greater than your CAC, which means you're just getting free customers now. Level three is where I like to live, which is that my 30-day gross profit is greater than two times the cost of getting a customer. Okay? So pay attention to what happens here. So you make gross profit more than twice CAC in the first 30 days, and the result is never being limited by money at all. Remember, the first version of this is, like, I'm limited by the amount of credit card that I can, uh, have access to. With this, there are no limits. And this is the goal of everything that I'm gonna basically go
```

## 31. `diagnostic_ltv_good_payback_bad::gross-profit:0`

**Query:** Lifetime gross profit is around $1,800 and CAC is $300, but it takes eight months to collect enough profit to cover CAC. What part of the money model should I work on?

**Query type:** `diagnostic_numeric`

**Chunk:** `gross-profit:0` from `gross-profit`

**Retriever ranks:** dense-openai rank 1, hybrid-rrf rank 2

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | Provides context on gross profit importance but does not directly address the user's specific money model issue. |
| Subagent first pass | gpt-5.5 | 1 | Useful for understanding gross profit and why customer value matters, but the query's main issue is slow payback timing. |

**Chunk text:**

```text
Gross profit. All right, let's rock in. So this is the second of the three metrics that we look at to triangulate acquisition. We started with CAC. You have to have cheap customers. We talked about the different ways to improve it, free or discount, different ways to display discounts. Uh, but now we're gonna talk about gross profit. Okay? So we're gonna define what it. is, why it's important, examples, calculating and improving it. All right, let's rock. So gross profit, the difference between the price and the cost of goods sold. So cost of goods or COGS is what it costs you to deliver the thing. All right? So if it cost me $9 to deliver meals and I sell it for 10, then I got $1 in. gross profit. All right? Very straightforward. Now, here's why this is important. So the problem is that most businesses think they need cheaper leads, when in reality they need to make more money per customer. And so my observation is that the CAC... This is, this is me, like high level, 'cause I see lots of businesses. CAC. between competitors is often fairly similar. So a lot of people are, you know, obsessing about how they're like, you know, they wanna improve their ads and things like that. And sometimes you do need to do that. But the ranges are actually much tighter than you'd think. So you might see somebody who's, you know, acquiring customers. at $2,500. Somebody and somebody else in the marketplace might be $3,500. Rarely would you see somebody at like $6,000 unless they're like just getting into the market. But the CAC for specific avatars is usually pretty tight in terms of ranges when I see many businesses in the same industry. Now that may surprise you, but that just like kind of is what it, is. But the difference between how much money these, these companies make is often how much customers are worth. Now that is where the huge discrepancy between businesses exists. So this is the difference between the whales and the minnows, is how much they make per customer, gross profit. All right? So let me tell you a quick story. So I did a consulting day years and years and years ago. This might have been the first five I've ever done in my whole life. Um, and a guy was in the same space as me. And you're like, "Wait, Alex, why would you help someone who's a quote competitor?" I don't see the world that way. So guy came in and he was selling the same number of units per month as me. All right? Same number of
```

## 32. `diagnostic_ltv_good_payback_bad::money-models-offer-stacks:0`

**Query:** Lifetime gross profit is around $1,800 and CAC is $300, but it takes eight months to collect enough profit to cover CAC. What part of the money model should I work on?

**Query type:** `diagnostic_numeric`

**Chunk:** `money-models-offer-stacks:0` from `money-models-offer-stacks`

**Retriever ranks:** bm25 rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Directly discusses structuring offers to maximize gross profit and minimize CAC, which is crucial for addressing the user's query. |
| Subagent first pass | gpt-5.5 | 2 | Defines a good money model as maximizing gross profit collected in the first 30 days, directly addressing slow payback despite strong LTV. |

**Chunk text:**

```text
[Full transcript for money-models-offer-stacks - 16 minutes of detailed content about money models and offer stacks, covering the rental car example, Gym Launch example, and offer sequencing strategies] So we just covered the three levels. Let's rock into money models and offer stacks. All right. So, uh, you will notice throughout this whole training that some of the things are a little bit different from the book, and that's done on purpose because I like to think through things differently in different mediums. All right? Because I can say things here that I couldn't normally say in the book. So we'll go definition, rental car story, and the gym launch example. All right. So a money model is a series of offers. That's it. The reason I had to start with the offers book before talking about the money model book is that an offer is one unit. A money model is sequencing these things. It's putting them in a series of offers deliberately to maximize gross profit collected in the first 30 days. So I will say this all together. A money model is a series of offers. A good money model, which is the objective of this book, or this training, is a series of offers structured to minimize CAC, how much it costs to get a customer, maximize gross profit, how much they pay you, collected in the first 30 days, how fast they pay you. That's the point... [Content continues with rental car counter story example including late checkout, insurance upgrade, minimum package, prepaid gas, and late return fees explanation] ...describing how rental car companies engineer their offers sequentially. The story illustrates 9 different upsells that occurred during a single reservation transaction. This is followed by the Gym Launch case study detailing how the company grew from $1,000 in the bank to $17 million in profit in 20 months through their money model approach. The transcript covers their specific offer stack including: free book/podcast lead magnet, free strategy call, $16,000 premium offer with payment terms, free supplement training, and free feedback call with continuity upsell. The lesson emphasizes how understanding offer sequencing and psychology can dramatically increase customer lifetime value and enable rapid scaling without external funding.
```

## 33. `diagnostic_ltv_good_payback_bad::how-businesses-make-money:1`

**Query:** Lifetime gross profit is around $1,800 and CAC is $300, but it takes eight months to collect enough profit to cover CAC. What part of the money model should I work on?

**Query type:** `diagnostic_numeric`

**Chunk:** `how-businesses-make-money:1` from `how-businesses-make-money`

**Retriever ranks:** bm25 rank 1, dense-openai rank 5, hybrid-rrf rank 1

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Illustrates the relationship between CAC and gross profit, providing a cautionary tale that aligns with the user's situation. |
| Subagent first pass | gpt-5.5 | 2 | Contrasts lifetime gross profit with 30-day gross profit and gives benchmark math, making it useful for diagnosing slow CAC recovery. |

**Chunk text:**

```text
## [§1.2.b] Meals company cautionary tale — revenue vs gross profit

Let me give you this, a real example to make this, make this real for you. So this was a real thing for me. So I had a meals company for a year or two, um, and foreshadowing, things went wrong. So we had a $100 CAC, which means it cost me $100 to get a customer, and we had $500 of lifetime revenue. I'm highlighting this, lifetime revenue. And I was like... And so my team comes to me and says, "Hey, we're gonna be rich. Every $100 we put in, we get $500 back. Let's spend more money." And I was like, "Hold on one second." And so not so fast. I was like, "Okay, well what are our gross margins on these meals?" And so the gross margins were 20%. So... And our lifetime revenue was 165 times three, meaning people would pay for $165 a week for the meals, and they would pay for three weeks. Okay. So the 30-day gross profit was, uh, was, um... Sorry, this is per month. Excuse me. Uh, so 165 times 20% is $33. So now my lifetime gross profit was 500 times 20% was $100. So wait a second. So you're saying I'm spending 100 making $33 back in the first month and spending 100 and making $100 back lifetime. But then we have like all these humans that we have to do all this other stuff with as well. Well, that's not gonna work very well. And so it didn't. And so I told them, to not do that. It's also why I'm not in the meals business anymore. Um, now if you're like, "Hey, why didn't you' work to figure it out?" It was the fourth business I started while I was still CEO, and Leila and I had one of these conversations. She's like, "Pick." I was like, "Legit." And so I ended up shutting that. down 'cause I had a co-packer, so it wasn't like I had a huge amount of, um, staff or something that I had to lay off or anything like that. I was repurposing my supplement company staff to deal with all the meal stuff. Here's a fun fact for you. Uh, 80% of our customer complaints came from meals, 20% from supplements, and 95% of my profits came from supplements, and 5% came from meals, and I was like, "I think if I were giving me advice, I would advise me to stop doing this." And so I did. So let me give you some benchmarks, though, so you have an idea, 'cause you're like, "Okay, got it." So LTP... LT... That should say GP, not PG. So it's not a PG-13 movie. Lifetime gross profit to CAC ratio should be over three to one, which means you should be able to make more than three times what it costs you to get a customer in gross profit, not revenue, gross profit back to you as a business owner, right? At minimum, in order to have a profitable business. At minimum. This, is, not like that's the goal. This is the, by all means, if you're below this, you're absolutely screwed. At three, you're still not like in great, you. know, in a great position. Ideally, it's much higher. Okay. Here's the example gone better. So in order for this CAC, to work for this, business, I would have to make $1,500, not $500, in, lifetime gross profit in order for this to make sense. So I had to be way higher in order for this to work, and it wasn't. Okay? So that's just to give you an idea of what kind of adjustments that I would have to make in order to make that business work, which I was like, "I don't know if I can conceivably do that," which ultimately led to me deciding not to.
```

## 34. `diagnostic_ltv_good_payback_bad::how-businesses-make-money:2`

**Query:** Lifetime gross profit is around $1,800 and CAC is $300, but it takes eight months to collect enough profit to cover CAC. What part of the money model should I work on?

**Query type:** `diagnostic_numeric`

**Chunk:** `how-businesses-make-money:2` from `how-businesses-make-money`

**Retriever ranks:** bm25 rank 4, hybrid-rrf rank 5

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Highlights the importance of CAC, gross profit, and payback period, which are essential metrics for the user's analysis. |
| Subagent first pass | gpt-5.5 | 2 | Directly identifies the three numbers and says the problematic metric is payback period, the speed of making CAC back. |

**Chunk text:**

```text
## [§1.2.c] The three numbers that matter — CAC, GP, Payback Period

Which then leads us to the only three numbers that matters, and this is what you need to write down. This is what you need to think with. All right? Now, this is not in the book, and you're like, "Wait a second, how are you not talking about this in the book?" It's 'cause no one can do math. So you're here, and you can do math. So if you're looking closely, you may notice that there's three numbers that make the biggest difference here. All right? So number one is CAC, which is the cost of our customer. The second. is the fact that I talk about this 30-day thing. Like, why am I talking about 30 days? And the third is gross profit, which those three, metrics triangulate acquisition, meaning getting new customers. CAC is how much it costs. GP is to make a profit. In short, PPD means payback period. How long it takes you to make that money back. How long it takes you to make your cost back. So ideally, you get, have low CAC, which means you have cheap customers. You have high GP, who pay you lots of money, and then short payback period, which means really fast. Outcome is more money faster. All right. And that's pretty much the training in this book. Like, that's what this is all about. So that's, that's what we accomplished. The rest of this is all about how. Okay? So boom, those are the three numbers that matter, and let's get into the first one in a little bit more detail, 'cause some of you guys are like, "CAC? Sounds like something my cat threw up." Understood. That's the next one.
```

## 35. `diagnostic_ltv_good_payback_bad::cac:12`

**Query:** Lifetime gross profit is around $1,800 and CAC is $300, but it takes eight months to collect enough profit to cover CAC. What part of the money model should I work on?

**Query type:** `diagnostic_numeric`

**Chunk:** `cac:12` from `cac`

**Retriever ranks:** dense-openai rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | Discusses CAC but lacks direct application to the user's specific situation regarding payback period. |
| Subagent first pass | gpt-5.5 | 0 | Covers attraction offers and improving CAC, but CAC is already good in the scenario and the issue is payback period. |

**Chunk text:**

```text
doing. Um, you splinter out the thing. Now, I talk about this at length in the $100 million offers course. I'm not gonna break it down now, but basically, lots of different components to your offer, you have lots of different features. You take one feature off. You say, "This feature is 99% off now." Great. That's where the discount is. And then you sell the rest of it. All right? And so whatever you break off, it has to be something that's well-understood or it's not gonna work. All right? That's kind of the thing I was talking about earlier. People have to have an understanding of it. Um, the cons are you got the bargain hoppers, right? People who, you know, complain about this, but really they, they're already, you know, uh, they're already customers. They're easier to upsell though than somebody who's cold. So yeah. All right. So the objective is that attraction offers are the first step in the four prongs because if you don't have interest, you don't have anything, right? And so customer-financed acquisition requires demand. And a big difference between CAC and GP, having low cost or free front ends is a strong way to do it. So lots of demand, free big front ends, drives more in. All right. So these things are going to be interchangeable throughout the remainder of these trainings. So if you see $19 chiropractor visit, it can be just as much a free chiropractor visit. The whole thing will work. But if you're like, you insist on doing this, fine, do that. If you insist on doing this, fine, do that. It does not matter. All the money models that I will show you can have free or discount interchange and they will both work. Kaboom. These are the ways that you can improve your CAC. So with that being said, CAC is covered. Now we go into gross profit.
```

## 36. `paraphrase_buy_more_units::ten-years-ten-minutes:3`

**Query:** Customers already want the thing. I want them to commit to more sessions up front without making it feel like a discount. What structure fits?

**Query type:** `paraphrase`

**Chunk:** `ten-years-ten-minutes:3` from `ten-years-ten-minutes`

**Retriever ranks:** hybrid-rrf rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | Discusses continuity offers and upselling strategies, but lacks specific structure for upfront commitment. |
| Subagent first pass | gpt-5.5 | 0 | Mentions waived-fee commitments and broad wrap-up, not buying more sessions up front via a reframed structure. |

**Chunk text:**

```text
there's four different places that you can spread it out, at the front, at the end, in the middle, in between. That's the point , spread out over the whole thing. But that is fundamentally how continuity offers work to get people to sign up. Then we have the wave fee offers. So first, you ask a customer to pay a startup fee as part of adjoining or month-to-month program. Then you offer a discount to the entire fee if they commit to the longer term. If they cancel inside the term, they pay you the fee. Freemium, which I didn't, I cut from this one. I'll make a YouTube video about it 'cause I think it really only applies to software, and I thought that was too niche. All right, you build money models one stage at a time. Once I get customers reliably, then I make sure that they pay for themselves reliably. Then I make sure that they pay for other customers reliably. Then I start maximizing each customer's long term value. Then I print as much money as I possibly can. Bottom line, the knowledge in these bullets brought me more free and profitable customers than I've known what to do with. If executed, they will do the same for you. And with that, cash will no longer be a constraint in your business. I hope that this book and this training helps you guys grow your dream as big as you darn well please. And that is 10 years in 10 minutes. So in the next one, we'll just put it all together and put a nice bow on it, and we'll wrap this puppy up.
```

## 37. `paraphrase_buy_more_units::buy-x-get-y:6`

**Query:** Customers already want the thing. I want them to commit to more sessions up front without making it feel like a discount. What structure fits?

**Query type:** `paraphrase`

**Chunk:** `buy-x-get-y:6` from `buy-x-get-y`

**Retriever ranks:** dense-openai rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 2 | Explains how prepaying customers are likely to buy more, which directly supports the query about committing to more sessions. |
| Subagent first pass | gpt-5.5 | 2 | Directly says buy-X-get-Y-free works for buying more or longer access and reframes pricing as free value. |

**Chunk text:**

```text
for fast cash. Now, if your business is healthy but you're like, "You know. what? I wanna buy a bunch of equipment," great. Prepay 10 people, go buy your equipment. Or you need to go buy a, uh, another big oven, industrial oven for your baking business. Like, totally makes sense for you to do prepayments and things like that to cash flow or fund rather than take on credit lines. Super smart. Um, so, even if customers prepay, you can still upsell them different stuff now. So this is really important. So I made this mistake, which is why I share it with you. The people who prepay, especially for services, for durations of time, business owners have this fear of selling them or making offers for other stuff. But here's the craziest thing that we saw, is that the people who prepay for the year are the most likely people to buy more stuff afterwards. And so these are basically a way of identifying your hyper buyers. And so they self-select. They prepay for a year, and guess what happens after that? When I would have Big Booty Boot Camp and a deadlift seminar or, you know, uh, Make Your Sexy Back or I would do Buns & Guns or whatever else I would do, Lean by Halloween, they were the most likely people to pay, 'cause guess what? They weren't paying anything for being there as far as they felt. They, they had paid so long ago they forgot that they paid. So it felt like I was just a free gym. And you know what? The cool thing about wallets with people who make money, they replenish and then you can ask again. So if customers only buy once, this is just a disclaimer for the, um, for the boot business. The reason they structured their deal that way was to maximize the transaction. So if you're in a business where people only buy once, then it makes sense to structure as much into that first sale as you can 'cause you're only gonna get one shot. Like the bachelorette parties are probably not coming back to Nashville. Now maybe they will, but for the most part, that's this... You wanna make the big, the ask as big as you can if you're only gonna get one shot. Summarizing buy X, get Y, free. In buy X, get Y free, customers buy something, they get other stuff for free. Buy X, get Y free. works, uh, for stuff that makes sense to buy more of or get longer access to. Basic buy X, get Y free, offers reframe pricing. Buy one, get two free, costs the
```

## 38. `paraphrase_buy_more_units::classic-upsell:0`

**Query:** Customers already want the thing. I want them to commit to more sessions up front without making it feel like a discount. What structure fits?

**Query type:** `paraphrase`

**Chunk:** `classic-upsell:0` from `classic-upsell`

**Retriever ranks:** bm25 rank 1

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | Provides insights on upselling but focuses more on the sales process than on upfront commitment structures. |
| Subagent first pass | gpt-5.5 | 0 | Classic upsell covers a next natural add-on, not committing to more units or sessions up front without a discount feel. |

**Chunk text:**

```text
## [§4.2.a] How I learned it — fur coat storage + the no-sell sale

All right. The classic upsell. As ush, how I learned it, description, examples, important points. Here's my lovely visual thing for the classic upsell. How I learned it, here' we go. So, uh, I had a mentorship, whatever you wanna call it. It, wasn't really a mentorship. I was just getting paid, and I took him as a mentor. He didn't really care about me at all. Um, uh, at a fur coat dealer, and, uh, he was a fourth generation furrier. And I, uh, remember watching how his son, who was my friend, that's how I got the job, uh, I'd be brushing fur coats all summer in the heat in the warehouse. Uh, unbelievably mind-melting stuff, like, boring beyond belief. And the thing that I kept thinking was that every single one of these coats was $200, and he had 7,000 coats in his warehouse. And I was like, "Holy cow." I was like, "That's $1.4 million that he's making just for storing coats for the summer." I was like, "This is pretty sweet." And I know what I was making, and it. was not $1.4 million for storing these coats. And so, the offer that they had to get people in was that they would get people to store their coats. And they said if they stored them, they would get free earmuffs, free fur earmuffs. So, people were like, "Oh, that's cool." And so, people would come in for the free earmuffs. And then they would say, "Uh, we'll store and condition the coat for you, and it costs 30 bucks to, uh, store the muffs." Now, they'd come in for free earmuffs, but it's the summer. So, then they would basically hand them the earmuffs and then take the earmuffs back, and then they'd say, "You don't want anything else, do you?" And so, by saying you don't want anything else, they would assume close the winter storage, the conditioning, and the earmuffs that went with the sale. And so, that is when I learned you can't have X without Y. And that is the fundamental basis of the classic upsell. You don't want burgers without fries. You don't want burgers without a Coke. You don't want a fur coat without storing it. You don't want a fur coat without conditioning it. It'd be like taking a car and not getting it serviced. Like, you don't want X without Y. And so, I learned a couple of things. One was the structure of a classic upsell, which is you don't want X without Y. But tactically, I learned the no-sell sale, all right? And so, the way that this works is basically people have been conditioned over the years to- to say no to salesmen. And so, when someone says you don't want anything else, most people just immediately say no. And so, what we wanna do is basically imply that the else means in addition to the thing we just offered you. And by doing that, you get people to say yes by saying no. And so, these people who came in to store their coats agreed to storage, conditioning, and the free earmuffs, which then got stored at a $30 fee for saying no, that you don't want anything else. So, the no-sell sale is what I ended up calling, uh, a different sale, which may sound confusing, but bear with me. So, if someone came into the gym and they said they... Ultimately, they declined every service offering we had, right? Which sucks. You would then try and salvage some sort of goodwill or rapport, 'cause this person walked in and is basically walking back out, which sucks. And so you say, "Hey, listen, I will still wanna help you for six weeks. And so, why don't we just do this as an at-home program, all right? So, I'll give you this thumb drive that has at-home workouts that you can follow, and then come in, in a couple days, and we will give you a nutrition consult on the house, all right? We just wanna help you out, and hopefully, maybe in... when things are a little less crazy or money's a little bit better, you can come back, and at least you'll have nice things to say about us." And so, a lot of people would say yes to that. And so, when they showed up to the next appointment, which was the nutrition consult, we would still close the same percentage of them as we did for normal customers. But here was the cool thing. We actually closed them at a higher average ticket. And so, the people who bought services and then bought supplements averaged $200 a ticket. People who didn't buy services and then bought supplements averaged $300 a ticket. And so, to me, my lesson from this was that we tried to solve their problem not in a way they wanted to solve it. So, they wanted to lose weight, but they wanted to have a magic pill rather than work. And so, we needed to have the magic pill available for them, which in their mind would be supplements. Now obviously, we always say, "Hey, you gotta make sure you eat the food," and all that stuff. But people hear what they wanna hear. And so, the thing is- is the magic behind this is that we turned no-sales into sales by just offering them something else.
```

## 39. `paraphrase_buy_more_units::ten-years-ten-minutes:2`

**Query:** Customers already want the thing. I want them to commit to more sessions up front without making it feel like a discount. What structure fits?

**Query type:** `paraphrase`

**Chunk:** `ten-years-ten-minutes:2` from `ten-years-ten-minutes`

**Retriever ranks:** bm25 rank 3, dense-openai rank 1, hybrid-rrf rank 1

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | Mentions various upsell strategies but lacks a clear structure for upfront commitment. |
| Subagent first pass | gpt-5.5 | 1 | Partially relevant because it mentions continuity commitments and related offer types, but not the buy-more-units structure. |

**Chunk text:**

```text
the most expensive thing first. If the customer balks, you offer a much cheaper and still acceptable alternative: "No worries. You don't care about X, this may be a better fit for you." D, rollover upsells, you credit some or all of a customer's previous purchase towards your next offer. "Since you already spent $500, I'll just credit that towards staying a full year." Pick your price, which I ended up not including this. I'll probably make a YouTube video about it. Downsell offers are whatever you offer after someone says no. That's my scientific, uh, answer for that. And by turning nos into yeses, you make more money. We covered three of my favorites. So payment plan downsells, you offer the same product at the same price, but they pay some now and the rest over time: "When do you get paid? Let's do half now and half then." Trial with penalty, you let customers try your product or service for free so long as they meet your terms. If they do, then they have a better chance of becoming paying customers. If they don't, they pay. "If you do X, Y, and Z, I'll let you start for free." Feature downsells, you lower prices by changing what the customer gets: "I offer lower quantity, lower quality, or lower priced alternatives, or cut optional components altogether." "If you're okay without a guarantee, I can knock off $400." That's how that works. Then we had continuity offers, which provide ongoing value that customers make ongoing payments for until they cancel. These boost the profit of every customer and give you one last thing to sell. We covered three of my favorites. Continuity bonus offers, so with a continuity bonus, you give the customer an awesome thing if they sign up today. Typically, the bonus itself is more value than the first continuity payment: "If you sign up today, you'll also get XYZ valuable thing." And if you want them to stick, you can continue to give them bonuses to maintain the service. Continuity discount offers we cover is the second type. We covered first month, backend commitments. And you give the customer free time now, an hour later, if they sign up today. And so the key point is that there's four different places that you can spread it out, at the front, at the end, in the middle, in between. That's the point , spread out over the whole thing. But that is fundamentally how continuity offers work to get people to sign up. Then we have the wave fee offers. So first, you ask a customer to pay a startup fee as part of adjoining or month-to-month program.
```

## 40. `diagnostic_free_offer_overload::gross-profit:3`

**Query:** Our free workshop dropped lead cost from $80 to $12, but sales booked per 100 leads fell and support time exploded. Is the free offer actually working?

**Query type:** `diagnostic_numeric`

**Chunk:** `gross-profit:3` from `gross-profit`

**Retriever ranks:** bm25 rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | Provides context on gross profit but does not directly address the impact of the free offer on sales or support time. |
| Subagent first pass | gpt-5.5 | 1 | Useful for factoring service/support cost into profitability, but it does not diagnose free-offer lead quality directly. |

**Chunk text:**

```text
of attention, he would outbid me every time. And our goal is to do the same to our competitors. All right? So you need to look at both sides, getting customers for less, but also making them worth more. All right? And before we improve it, we gotta know how to calculate it. So here's gross profit, how we calculate it. So here's a product example. So if I sell a widget for $100, it costs me 20 bucks to manufacture it and ship the widget to the end customer. All right? So my gross profit is 100, where it is, 100 minus 20, 80 bucks. This is what's left over. This is my gross profit. Okay. Here's a service example. Let's say I deliver services monthly and I have one account representative per ten customers. If my clients pay me $3,000 per month each and my reps cost me $6,000 per month, we can then figure out the gross profit margin. Okay.So the rep salary is six thousand dollars. The clients per rep is ten. The cost per client means it's six hundred dollars per client. Remember, we make six thousand dollars, divided by ten clients, six hundred dollars per client. Gross profit, all right, is now three thousand dollars, what they' pay us, minus my cost per client, which means twenty-four hundred left over. The reason I'm going through this is that many of you, guys watching this are service-based businesses and don't know your costs. These, are your costs. So my gross margins are twenty-four hundred divided by three thousand dollars, which is 80%. Rule of thumb from Alex, if you run a service-based business, local brick and mortar or national, you want at least an 80% gross profit margin. Now that- that may sound crazy to you, but it is very unlikely that you will scale in service unless you have 80 or higher. So not just eight- that means that if it cost you a hundred, you gotta sell it for five hundred. Now you might think, 'cause if you're a newer business owner, you're like, "No, I- that's- that seems unreasonable." That's your gross profit, not your net profit. You still have rent. You've got, you've got your fixed admin cost, you've got insurance, you've got utilities, you've got break-fix that happens within your business. You've got all these other costs that go into doing business. You're not running 80% net margins. You're just saying this is now all the money I have left over to run the re- I still gotta spend advertising dollars. Like there's all this money that I still gotta spend. And so if you're- if you're at 80, you
```

## 41. `diagnostic_free_offer_overload::cac:2`

**Query:** Our free workshop dropped lead cost from $80 to $12, but sales booked per 100 leads fell and support time exploded. Is the free offer actually working?

**Query type:** `diagnostic_numeric`

**Chunk:** `cac:2` from `cac`

**Retriever ranks:** dense-openai rank 4, hybrid-rrf rank 3

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | Discusses customer acquisition cost (CAC) but does not specifically relate to the effectiveness of the free offer. |
| Subagent first pass | gpt-5.5 | 1 | Background on CAC levers and free/new as advertising tools; it sets context but does not address the support overload problem. |

**Chunk text:**

```text
spent $35,000 divided by 10 customers, $3,500 per customer is our CAC. That's how this works. By the way, one of the best ways to improve any metric is to start measuring it. So, how to improve it? In this whole training, I talk about lots of different things that cover and check off different boxes here. But fundamentally, if you had nothing else and you just wanted to have a cheat sheet for this, it would be, you make better offers, that gets you higher response rates. And if you make better offers, you're also gonna convert a higher percentage of people, more people are gonna take the next step. Uh, if you have better offers in general, your CPMs are also gonna go down because people are like, "Oh, this is a better offer." Great. Uh, you'll have cheaper labor, so you won't necess- like, this is not necessarily related, but you could have cheaper labor as a way to improve CAC, like if you had, if you paid your sales guys less or you paid the outbound team less, whatever it is, like that could decrease your CAC. Uh, and you could have cheaper software because that is also a cost. But I would say if I had to measure which of these is gonna be the biggest levers, it's gonna be these three. And I would, I rarely go and dip into these ones, to be very candid with you, because you have such order of magnitude changes you can make up here that sometimes this stuff becomes irrelevant. You lose morale for no real, no real benefit. All right? So we talk about these two primarily for this book. So the two most powerful words in advertising are free and new. Use, them. And so for us, if our objective is to lower CAC to the greatest degree possible, we wanna get as many sales as possible for as little advertising dollars as possible. And so that means we wanna convert the highest percentage of our audience. And so note that this is expanded content from the book, all right, that I just think is worth knowing. All right? So in 100 Million Dollar Leads, I talk about the value of giving something away for free. Some people don't wanna do that, but let me explain why I think it's probably a good idea, especially if you're starting out. All right. So Dan Ariely, again, the- none of this is in the book, I had to cut this out. So Dan Ariely, who's a famous behavioral economist, psychologist, whatever, some science dude. All right. So he ran this thing called the Hershey Kiss test. And
```

## 42. `diagnostic_free_offer_overload::cac:1`

**Query:** Our free workshop dropped lead cost from $80 to $12, but sales booked per 100 leads fell and support time exploded. Is the free offer actually working?

**Query type:** `diagnostic_numeric`

**Chunk:** `cac:1` from `cac`

**Retriever ranks:** bm25 rank 5, hybrid-rrf rank 4

| Label Source | Model | Relevance | Note |
|---|---|---:|---|
| OpenAI first pass | gpt-4o-mini | 1 | Explains how to calculate CAC, which is relevant but does not directly answer the query about the free offer's effectiveness. |
| Subagent first pass | gpt-5.5 | 1 | Useful background for calculating fully loaded CAC from leads and sales, but not direct evidence about whether the free workshop is working. |

**Chunk text:**

```text
business owner. So this is how we, this is how we calculate it. So the total cost for eight sales means that you have a $3,000 emailer plus a $200 software plus 800 bucks in commissions, which is eight sales times $100 equals four grand. All right? So now, we divide that by the number of new customers, which is $4,000 divided by eight new customers equals 500 bucks per sale. So CAC. is $500 in this outreach example. So let's say that you have a content business. So let's do this one. So you have to pay two people on your media team that you pay $5,000 a month each, and they help you make, edit and distribute content across all platforms, right? So that content then turn into inbound messages and then opt-ins on your site, and then those leads turn into 10 new customers and you pay $100 in commission per sale. All right. So what's CAC? So the reason I'm giving you all those stats is so that you can plug your own stats in and then figure this out for yourself. So if my media payroll is 5K times two, it's $10,000 a month there, my commissions is 10 sales times 100 is 1,000. So all in I got 10 grand plus one grand is $11,000. So my cost to acquire a customer we'll say is $11,000 divided by 10 customers equals $1,100. So my CAC's 1100 bucks. Now if some of you are like, "Wait, I have sales payroll in there too," then add it in. If there's something that you don't have here, cut it out. But fundamentally it's just all the money you spend to get new customers divided by how many customers you got. Cool. And I'll do one quick one on paid ads. So you spend $4,000 a month on a media buyer, you spend 20 grand in buying ads, the actual media itself. You spend 1,000 bucks commissions per sale, so this is probably a higher ticket sale, and you spend $1,000 on software and tracking and following up with leads that come in to get 10 new customers. So what's CAC? So media, 4K, media spend, 20K, software, 1K, commissions, 10 times one, 10,000. So all in, we spent $35,000 divided by 10 customers, $3,500 per customer is our CAC. That's how this works. By the way, one of the best ways to improve any metric is to start measuring it. So, how to improve it? In this whole training, I talk about lots of different things that cover and check off different boxes here. But fundamentally, if you had nothing else and you just wanted to have
```
