/* About Wholehearted. Editorial content only; does not read or write prayer data. */
(function (root) {
  'use strict';
  const POEM = Object.freeze([
    'Inside the quiet chambers of the chest,',
    'The Heart beats out its steady, sacred drum,',
    'While Emotions rise like oceans, manifest,',
    'Stirring the deep where quiet shadows come.',
    'The Will stands firm, a beacon in the night,',
    'Guiding the steps through storms that wildly roll,',
    'As the sharp Mind unravels dark to light,',
    'All held within the eternal, breathing Soul.',
    'When these five rivers gather and collide,',
    'The fragile banks of ordinary break;',
    'We are whelmed beneath the brilliant, rising tide,',
    'Alive to every truth they leave awake.'
  ]);
  const DESCRIPTION = 'W.H.E.M.S. Prayer brings our Will, Heart, Emotions, Mind and Soul before God when seeking his help and direction. We thank him for the areas he has already shaped and ask him to transform the areas that are still struggling, so that our decision and response honour Christ.';
  const esc = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const link = (url, text) => `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(text)} <span aria-hidden="true">↗</span></a>`;
  const bible = ref => link('https://www.esv.org/verses/' + encodeURIComponent(ref).replace(/%20/g,'+').replace(/%3A/g,':') + '/', ref + ' · ESV');
  const AREAS = [
    ['W','Will','What am I willing to do?','Bring your choices and reluctance before God. Ask for willingness to obey rather than merely for your preferred outcome.','Luke 22:42'],
    ['H','Heart','Why do I want this?','Examine what you love, desire or protect. Give thanks for love already growing and ask God to search your motives.','Psalm 139:23-24'],
    ['E','Emotions','What am I feeling?','Bring joy, grief, anger or fear honestly. Ask for help with your response, without treating a feeling as a command from God.','Matthew 26:37-39'],
    ['M','Mind','What is true and wise?','Consider Scripture in context, distinguish facts from assumptions and receive sound counsel. Ask for renewed understanding.','Romans 12:1-2'],
    ['S','Soul','Whose am I?','Bring your life and allegiance before God. For the person trusting Christ, grace is the foundation of obedience, not a reward for completing this exercise.','Ephesians 2:8-10']
  ];
  function content() {
    return `<article class="about-copy">
<header class="about-intro"><p class="eyebrow">The story behind W.H.E.M.S. Prayer</p><h3>A prayer can hold both <br>gratitude and struggle.</h3><p>${DESCRIPTION}</p><p><strong>Wholehearted</strong> is the app. <strong>W.H.E.M.S. Prayer</strong> is the simple structure within it. Here, wholehearted does not mean that every thought or feeling is already settled. It means bringing the whole matter before God, willing to be taught and changed.</p></header>
<details class="about-section" open><summary>How the idea began</summary>
<p>The first exchange considered material about prayer and decision-making, including the reorientation of the heart, emotions, will and mind towards God. Adrian then asked which godly people are remembered for these qualities in lives devoted to serving God. It began with a Bible-study question, not a plan to build an app.</p>
<p>In the September 2026 conversation, Adrian explored that question with ChatGPT. The discussion considered David’s Godward heart (${bible('Acts 13:22')}), Hannah’s honest distress in prayer (${bible('1 Samuel 1:15')}), Daniel’s resolve (${bible('Daniel 1:8')}) and Ezra’s commitment to study, practise and teach God’s Word (${bible('Ezra 7:10')}). These were illustrative emphases, not personality types or claims that each person possessed only one quality.</p>
<p>Adrian then asked how discipleship to Christ and the fruit of the Spirit could be brought together under <strong>Will, Heart, Emotions, Mind and Soul</strong>. His clarification gave the idea its purpose: to <q>seek help to make decisions or praise God for his direction</q>.</p>
<p>The aim became a prayer aid that a new believer could learn in a few minutes: thank God for the help already evident, ask for help where struggle remains, and seek a response that honours Christ. The website came afterwards, to make that practice easier to use and revisit.</p>
</details>
<details class="about-section"><summary>From HEWMS to W.H.E.M.S.</summary>
<p>The early material played with two arrangements of the same letters: <strong>HEWMS</strong> - Heart, Emotions, Will, Mind, Soul - and <strong>WHEMS</strong> - Will, Heart, Emotions, Mind, Soul. It also played on the sound of <em>whelm</em>, picturing the experience of being deeply moved or overwhelmed.</p>
<p>That wordplay gave the conversation an image, not a doctrine. W.H.E.M.S. is used here as a memory aid for prayer. The letters do not establish a mandatory order, five independent parts of a person, or a formula for discovering God’s hidden will.</p>
<p>The name <strong>Wholehearted</strong> expresses the direction of the practice: not making every inner voice agree with our preference, but bringing ourselves before God under his Word. ${bible('Romans 12:1-2')}</p>
</details>
<details class="about-section"><summary>The original poem</summary>
<p class="about-source-note">Original creative material supplied in the founding conversation. Adrian introduced it as coming from <q>another LLM</q> - another AI language model. The specific model and authorship were not identified. The wording below is preserved; this is not presented as Scripture or a historic Christian prayer.</p>
<blockquote class="about-poem" aria-label="Original poem supplied in the founding conversation">${POEM.map((line, i) => `<span class="poem-line${i && i % 4 === 0 ? ' stanza-start' : ''}">${esc(line)}</span>`).join('')}</blockquote>
<h4>What the imagery expresses</h4>
<p>The heart becomes a drum, emotions an ocean, the will a beacon and the mind a movement from darkness towards light. The soul is pictured as holding that lived experience together. The gathering rivers describe how a decision can involve the whole person, rather than reasoning alone. This is a reading of the poem’s imagery, not a biblical definition of human nature.</p>
<h4>Read the imagery with care</h4>
<p>The accompanying prose and meditation also described the soul as a <q>silent, timeless observer</q>. Wholehearted does not adopt that as its biblical definition. Nor is the poem’s <q>eternal, breathing Soul</q> taken here to mean that a human soul is uncreated or divine. The poem is retained as part of the origin story; the prayer framework is tested by Scripture.</p>
<p>Hannah pours out her soul before the Lord, and Jesus speaks of profound sorrow in his soul. These passages present a person bringing real distress to God, not merely an untouched observer of passing thoughts. ${bible('1 Samuel 1:15')} · ${bible('Matthew 26:37-39')}</p>
</details>
<details class="about-section"><summary>Five invitations before God</summary>
<p>These questions are teaching applications of the linked passages. They are invitations to honest prayer, not a test that must be completed.</p>
<dl class="about-areas">${AREAS.map(([key,name,question,body,ref]) => `<div><dt><span class="about-letter" aria-hidden="true">${key}</span><span>${name}<small>${question}</small></span></dt><dd><p>${body}</p>${bible(ref)}</dd></div>`).join('')}</dl>
<p>Biblical language overlaps. Ezra, for example, sets his <em>heart</em> to study, obey and teach - activities that involve thought, desire and action together. The categories help us notice what to pray about; they do not divide us into separate compartments. ${bible('Ezra 7:10')}</p>
</details>
<details class="about-section"><summary>Soul: saved by grace, freed to serve God</summary>
<p>Adrian’s original concern for S was <q>Saved or Slave to Sin</q>. The subsequent explanation expressed this as <strong>enslaved to sin, or saved by Christ and freed to serve God</strong>. Paul describes freedom from sin’s mastery as a new allegiance to righteousness and to God. ${bible('Romans 6:17-23')}</p>
<p>Soul is therefore not a fifth performance score. Salvation is God’s gift by grace through faith; good works follow rather than earn it. The purpose of this invitation is to remember whose we are and seek a life consistent with that belonging. ${bible('Ephesians 2:8-10')}</p>
<p>A difficult feeling or an unfinished struggle does not, by itself, determine whether someone is saved. Wholehearted does not make that judgement, assume the user’s faith, or treat the human soul as interchangeable with the Holy Spirit. Jesus’ sorrow in Gethsemane also keeps us from confusing emotional ease with obedience. ${bible('Matthew 26:37-39')}</p>
</details>
<details class="about-section"><summary>The turning point: three areas and two</summary>
<p>A practical question made the framework clearer: what happens when three areas seem consistent with our Christian testimony, but two still need help? And when help comes in those two areas, how do we return with thanks?</p>
<p>The answer became the central practice of Wholehearted: <strong>thank God for what he has helped, and ask for help where you are still struggling - in the same prayer.</strong> Paul joins requests with thanksgiving in ${bible('Philippians 4:6-7')}.</p>
<p>For example, after an unfair criticism, someone might understand the truth, be willing to pause, and remember their belonging to Christ, yet still want to embarrass the other person and feel intensely angry.</p>
<blockquote class="about-example"><p>Father, thank you for helping me understand what is right, become willing to pause, and remember that I belong to Christ. You also see my desire to hurt back and the anger I am carrying. Correct my motives and help me answer with love and gentleness.</p></blockquote>
<p class="about-source-note">Illustrative prayer, adapted from the original teaching example; not Scripture.</p>
<p>Later, the person may thank God specifically for a softened motive and a restrained response, even while still feeling hurt. The reverse is also possible: thank God for help in two areas while seeking help in three. Thanksgiving and a request may even sit within the same area.</p>
<p>This is not a majority vote. Three areas of gratitude do not permit an unkind act. Equally, a painful emotion need not prevent faithful obedience. Jesus prayed through deep sorrow while submitting to his Father. ${bible('Matthew 26:37-39')}</p>
</details>
<details class="about-section"><summary>Discipleship and the Spirit’s fruit</summary>
<p>The founding request connected W.H.E.M.S. with following Christ and the fruit of the Spirit: <strong>love, joy, peace, patience, kindness, goodness, faithfulness, gentleness and self-control</strong>. These describe the character of our response, not a prediction that a chosen outcome will succeed. ${bible('Galatians 5:22-25')}</p>
<p>The earlier discussion suggested useful connections: love with the heart, patience with emotions and will, and self-control with thoughts and actions. These are teaching associations, not exclusive assignments. All nine qualities concern the whole life of a disciple.</p>
<p>The goal is not to become certain that God endorses our preference. It is to learn, pray, obey what Scripture makes clear, receive correction and entrust the outcome to him. In the Gethsemane passages, Jesus directs prayer towards the Father’s will rather than simply the removal of distress. ${bible('Luke 22:42')}</p>
</details>
<details class="about-section"><summary>Sources, authorship and the role of AI</summary>
<p><strong>Origin record.</strong> This account draws on Adrian’s founding Bible-study exchanges in September 2026, including the request for a five-minute teaching. The poem is reproduced from the text he supplied. The surrounding explanation is an editorial account, not a verbatim transcript of the entire conversation. This records the development of this project; it does not establish that no one else has used a similar mnemonic.</p>
<p><strong>Human intention and AI assistance.</strong> Adrian supplied the purpose, theological questions and practical use case. ChatGPT helped organise explanations, examples and website development. The poem was supplied as material from another, unidentified language model. None of these contributions replaces Scripture, personal responsibility or the care of a church community.</p>
<p><strong>Scripture.</strong> ${link('https://www.esv.org/','ESV.org')} is the Bible-reading source. Scripture references above support the explanations; the W.H.E.M.S. arrangement remains a teaching application. No claim is made that these five letters appear as a prayer method in the Bible.</p>
<p><strong>Further study.</strong> ${link('https://www.stepbible.org/?q=version%3DESV%7Creference%3DPhil.4.6','STEP Bible · Philippians 4:6')} and ${link('https://www.blueletterbible.org/esv/phl/4/','Blue Letter Bible · Philippians 4')} provide places to examine the passage and its language. These links are not a claim of live lexical verification. ${link('https://app.logos.com/','Your Logos account')} opens separately; the app does not access your owned library.</p>
<p><strong>The website itself.</strong> The current prayer composer uses local templates and your wording, not live AI calls. Saving is local to this browser; HTML downloads are separate reading copies. An AI-assisted origin does not mean your personal prayer is sent to an AI.</p>
<p class="about-source-note">Editorial source review: 20 September 2026. Original conversation and supplied creative text; biblical references checked against ESV source material. No institutional endorsement or ancient provenance is claimed for W.H.E.M.S.</p>
</details>
<section class="about-ending"><h3>Begin with one sentence.</h3><blockquote class="about-example"><p>Father, thank you for ______; please help me with ______, so that my decision and response honour Christ.</p></blockquote><p>Bring what is grateful. Bring what is struggling. Let God’s Word, rather than the framework, have the final say.</p></section>
</article>`;
  }
  function mount(doc) {
    const trigger = doc.querySelector('[data-about-open]');
    if (!trigger || doc.getElementById('wholehearted-about')) return;
    const panel = doc.createElement('dialog');
    panel.id = 'wholehearted-about';
    panel.className = 'about-dialog';
    panel.setAttribute('aria-labelledby', 'about-heading');
    // Static editorial markup only. Never interpolate prayer records into this panel.
    panel.innerHTML = `<div class="about-bar"><h2 id="about-heading" tabindex="-1">About Wholehearted</h2><button type="button" data-about-close aria-label="Close About Wholehearted">Close</button></div><div class="about-scroll">${content()}<button type="button" class="secondary about-return" data-about-close>Return to where I was</button></div>`;
    doc.body.append(panel);
    let opener = null;
    let modal = false;
    function restore() {
      doc.documentElement.classList.remove('about-is-open');
      if (opener?.isConnected) opener.focus({preventScroll:true});
      opener = null;
    }
    function close() {
      if (modal && panel.open) panel.close();
      else {panel.removeAttribute('open'); restore();}
    }
    panel.addEventListener('close', restore);
    panel.addEventListener('click', event => {
      if (event.target.closest('[data-about-close]')) close();
    });
    panel.addEventListener('keydown', event => {
      if (!modal && event.key === 'Escape') {event.preventDefault(); close();}
    });
    trigger.addEventListener('click', () => {
      opener = doc.activeElement;
      modal = typeof panel.showModal === 'function';
      panel.classList.toggle('about-inline', !modal);
      if (modal) {panel.showModal(); doc.documentElement.classList.add('about-is-open');}
      else panel.setAttribute('open', '');
      panel.querySelector('.about-scroll').scrollTop = 0;
      panel.querySelector('#about-heading').focus({preventScroll:modal});
    });
  }
  const api = Object.freeze({POEM, DESCRIPTION, content});
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {root.WholeheartedAbout = api; mount(root.document);}
})(typeof globalThis !== 'undefined' ? globalThis : this);
